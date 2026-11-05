from typing import Annotated

from fastapi import APIRouter, Path

from ..db import fetch_all, fetch_one, get_connection
from ..deps import AnyUser

router = APIRouter(prefix="/reportes", tags=["reportes"])

IdTorneo = Annotated[int, Path(gt=0)]

_GOLES_CREDITADOS = """
    SELECT g.id_partido,
           CASE
               WHEN g.autogol = 1 AND pp.id_equipo = p.id_equipo_local
                   THEN p.id_equipo_visitante
               WHEN g.autogol = 1
                   THEN p.id_equipo_local
               ELSE pp.id_equipo
           END AS id_equipo_gol
    FROM gol g
    JOIN planilla_partido pp
      ON pp.id_partido = g.id_partido AND pp.ci_jugador = g.ci_jugador
    JOIN partido p ON p.id_partido = g.id_partido
"""


@router.get("/{id_torneo}/posiciones")
def tabla_posiciones(id_torneo: IdTorneo, user: AnyUser):
    sql = f"""
        WITH goles_creditados AS ({_GOLES_CREDITADOS}),
        marcadores AS (
            SELECT p.id_partido, p.id_equipo_local, p.id_equipo_visitante,
                   COALESCE(SUM(gc.id_equipo_gol = p.id_equipo_local), 0) AS goles_local,
                   COALESCE(SUM(gc.id_equipo_gol = p.id_equipo_visitante), 0) AS goles_visitante
            FROM partido p
            LEFT JOIN goles_creditados gc ON gc.id_partido = p.id_partido
            WHERE p.id_torneo = %s AND p.estado = 'jugado'
            GROUP BY p.id_partido, p.id_equipo_local, p.id_equipo_visitante
        ),
        resultados AS (
            SELECT id_equipo_local AS id_equipo, goles_local AS gf, goles_visitante AS gc,
                   goles_local > goles_visitante AS gano,
                   goles_local = goles_visitante AS empato
            FROM marcadores
            UNION ALL
            SELECT id_equipo_visitante, goles_visitante, goles_local,
                   goles_visitante > goles_local,
                   goles_visitante = goles_local
            FROM marcadores
        )
        SELECT e.id_equipo, e.nombre AS equipo,
               COUNT(r.id_equipo) AS partidos_jugados,
               COALESCE(SUM(r.gano), 0) AS partidos_ganados,
               COALESCE(SUM(r.empato), 0) AS partidos_empatados,
               COUNT(r.id_equipo) - COALESCE(SUM(r.gano), 0) - COALESCE(SUM(r.empato), 0) AS partidos_perdidos,
               COALESCE(SUM(r.gf), 0) AS goles_favor,
               COALESCE(SUM(r.gc), 0) AS goles_contra,
               COALESCE(SUM(r.gf - r.gc), 0) AS diferencia_goles,
               COALESCE(SUM(r.gano * 3 + r.empato), 0) AS puntos
        FROM equipo e
        LEFT JOIN resultados r ON r.id_equipo = e.id_equipo
        WHERE e.id_torneo = %s
        GROUP BY e.id_equipo, e.nombre
        ORDER BY puntos DESC, diferencia_goles DESC, goles_favor DESC, equipo
    """
    with get_connection(user.rol) as conn:
        return fetch_all(conn, sql, (id_torneo, id_torneo))


@router.get("/{id_torneo}/goleadores")
def tabla_goleadores(id_torneo: IdTorneo, user: AnyUser):
    with get_connection(user.rol) as conn:
        return fetch_all(
            conn,
            """
                SELECT j.ci, CONCAT(j.nombre, ' ', j.apellido) AS jugador,
                       e.nombre AS equipo, f.nombre AS facultad, COUNT(*) AS goles
                FROM gol g
                JOIN partido p ON p.id_partido = g.id_partido AND p.estado = 'jugado'
                JOIN planilla_partido pp
                  ON pp.id_partido = g.id_partido AND pp.ci_jugador = g.ci_jugador
                JOIN jugador j ON j.ci = g.ci_jugador
                JOIN equipo e ON e.id_equipo = pp.id_equipo
                JOIN facultad f ON f.id_facultad = e.id_facultad
                WHERE p.id_torneo = %s AND g.autogol = FALSE
                GROUP BY j.ci, j.nombre, j.apellido, e.nombre, f.nombre
                ORDER BY goles DESC, jugador
                LIMIT 10
            """,
            (id_torneo,),
        )


@router.get("/{id_torneo}/fair-play")
def tabla_fair_play(id_torneo: IdTorneo, user: AnyUser):
    with get_connection(user.rol) as conn:
        return fetch_all(
            conn,
            """
                SELECT e.id_equipo, e.nombre AS equipo,
                       COALESCE(SUM(t.color = 'amarilla'), 0) AS tarjetas_amarillas,
                       COALESCE(SUM(t.color = 'roja'), 0) AS tarjetas_rojas,
                       COALESCE(SUM(CASE t.color WHEN 'amarilla' THEN 1 WHEN 'roja' THEN 3 ELSE 0 END), 0) AS puntos_fair_play
                FROM equipo e
                LEFT JOIN planilla_partido pp ON pp.id_equipo = e.id_equipo
                LEFT JOIN partido p ON p.id_partido = pp.id_partido
                    AND p.id_torneo = e.id_torneo AND p.estado = 'jugado'
                LEFT JOIN tarjeta t ON t.id_partido = pp.id_partido
                    AND t.ci_jugador = pp.ci_jugador AND p.id_partido IS NOT NULL
                WHERE e.id_torneo = %s
                GROUP BY e.id_equipo, e.nombre
                ORDER BY puntos_fair_play ASC, e.nombre
            """,
            (id_torneo,),
        )


@router.get("/{id_torneo}/goles-por-fecha")
def promedio_goles_por_fecha(id_torneo: IdTorneo, user: AnyUser):
    with get_connection(user.rol) as conn:
        return fetch_all(
            conn,
            """
                SELECT p.numero_fecha,
                       COUNT(DISTINCT p.id_partido) AS partidos_jugados,
                       COUNT(g.id_gol) AS goles,
                       ROUND(COUNT(g.id_gol) / NULLIF(COUNT(DISTINCT p.id_partido), 0), 2) AS promedio_goles
                FROM partido p
                LEFT JOIN gol g ON g.id_partido = p.id_partido
                WHERE p.id_torneo = %s AND p.estado = 'jugado'
                GROUP BY p.numero_fecha
                ORDER BY p.numero_fecha
            """,
            (id_torneo,),
        )


@router.get("/{id_torneo}/uso-canchas-turnos")
def uso_canchas_y_turnos(id_torneo: IdTorneo, user: AnyUser):
    with get_connection(user.rol) as conn:
        canchas = fetch_all(
            conn,
            """
                SELECT c.nombre AS complejo, p.nombre_cancha AS cancha,
                       COUNT(*) AS partidos_jugados
                FROM partido p
                JOIN complejo c ON c.id_complejo = p.id_complejo
                WHERE p.id_torneo = %s AND p.estado = 'jugado'
                GROUP BY c.id_complejo, c.nombre, p.nombre_cancha
                ORDER BY partidos_jugados DESC, complejo, cancha
            """,
            (id_torneo,),
        )
        turnos = fetch_all(
            conn,
            """
                SELECT t.id_turno, TIME_FORMAT(t.hora_inicio, '%%H:%i') AS hora_inicio,
                       TIME_FORMAT(t.hora_fin, '%%H:%i') AS hora_fin,
                       COUNT(*) AS partidos_jugados
                FROM partido p
                JOIN turno t ON t.id_turno = p.id_turno
                WHERE p.id_torneo = %s AND p.estado = 'jugado'
                GROUP BY t.id_turno, t.hora_inicio, t.hora_fin
                ORDER BY partidos_jugados DESC, t.hora_inicio
            """,
            (id_torneo,),
        )
    return {"canchas": canchas, "turnos": turnos}


@router.get("/jugadores-por-facultad-tipo")
def jugadores_por_facultad_y_tipo(user: AnyUser):
    with get_connection(user.rol) as conn:
        return fetch_all(
            conn,
            """
                SELECT f.id_facultad, f.nombre AS facultad, tipos.tipo,
                       COUNT(j.ci) AS cantidad_jugadores
                FROM facultad f
                CROSS JOIN (
                    SELECT 'grado' AS tipo
                    UNION ALL SELECT 'posgrado'
                    UNION ALL SELECT 'docente'
                    UNION ALL SELECT 'funcionario'
                ) tipos
                LEFT JOIN jugador j
                  ON j.id_facultad = f.id_facultad AND j.tipo = tipos.tipo
                GROUP BY f.id_facultad, f.nombre, tipos.tipo
                ORDER BY f.nombre, FIELD(tipos.tipo, 'grado', 'posgrado', 'docente', 'funcionario')
            """,
        )


@router.get("/{id_torneo}/jugadores-sin-planilla")
def jugadores_sin_planilla(id_torneo: IdTorneo, user: AnyUser):
    with get_connection(user.rol) as conn:
        return fetch_all(
            conn,
            """
                SELECT j.ci, CONCAT(j.nombre, ' ', j.apellido) AS jugador,
                       e.nombre AS equipo, f.nombre AS facultad
                FROM equipo_jugador_torneo ejt
                JOIN equipo e ON e.id_equipo = ejt.id_equipo AND e.id_torneo = ejt.id_torneo
                JOIN jugador j ON j.ci = ejt.ci_jugador
                JOIN facultad f ON f.id_facultad = j.id_facultad
                WHERE ejt.id_torneo = %s
                  AND NOT EXISTS (
                      SELECT 1
                      FROM planilla_partido pp
                      JOIN partido p ON p.id_partido = pp.id_partido
                      WHERE p.id_torneo = ejt.id_torneo
                        AND pp.id_equipo = ejt.id_equipo
                        AND pp.ci_jugador = ejt.ci_jugador
                  )
                ORDER BY e.nombre, j.apellido, j.nombre
            """,
            (id_torneo,),
        )


@router.get("/{id_torneo}/sanciones-por-equipo-motivo")
def sanciones_por_equipo_y_motivo(id_torneo: IdTorneo, user: AnyUser):
    with get_connection(user.rol) as conn:
        return fetch_all(
            conn,
            """
                SELECT e.id_equipo, e.nombre AS equipo, motivos.motivo,
                       COUNT(s.id_sancion) AS cantidad_sanciones
                FROM equipo e
                CROSS JOIN (
                    SELECT 'roja' AS motivo
                    UNION ALL SELECT 'acumulacion de amarillas'
                    UNION ALL SELECT 'disciplinaria'
                ) motivos
                LEFT JOIN equipo_jugador_torneo ejt
                  ON ejt.id_equipo = e.id_equipo AND ejt.id_torneo = e.id_torneo
                LEFT JOIN sancion_jugador s
                  ON s.ci_jugador = ejt.ci_jugador
                 AND s.id_torneo = ejt.id_torneo
                 AND s.motivo = motivos.motivo
                WHERE e.id_torneo = %s
                GROUP BY e.id_equipo, e.nombre, motivos.motivo
                ORDER BY e.nombre, FIELD(motivos.motivo, 'roja', 'acumulacion de amarillas', 'disciplinaria')
            """,
            (id_torneo,),
        )


@router.get("/{id_torneo}/estado-partidos")
def porcentaje_estado_partidos(id_torneo: IdTorneo, user: AnyUser):
    with get_connection(user.rol) as conn:
        return fetch_one(
            conn,
            """
                SELECT
                    SUM(estado = 'jugado') AS jugados,
                    SUM(estado = 'postergado') AS postergados,
                    SUM(estado = 'cancelado') AS cancelados,
                    SUM(estado IN ('jugado', 'postergado', 'cancelado')) AS total_considerado,
                    ROUND(100 * SUM(estado = 'jugado') /
                        NULLIF(SUM(estado IN ('jugado', 'postergado', 'cancelado')), 0), 2) AS porcentaje_jugados,
                    ROUND(100 * SUM(estado = 'postergado') /
                        NULLIF(SUM(estado IN ('jugado', 'postergado', 'cancelado')), 0), 2) AS porcentaje_postergados,
                    ROUND(100 * SUM(estado = 'cancelado') /
                        NULLIF(SUM(estado IN ('jugado', 'postergado', 'cancelado')), 0), 2) AS porcentaje_cancelados
                FROM partido
                WHERE id_torneo = %s
            """,
            (id_torneo,),
        )


@router.get("/{id_torneo}/resultados-localia")
def resultados_localia(id_torneo: IdTorneo, user: AnyUser):
    sql = f"""
        WITH goles_creditados AS ({_GOLES_CREDITADOS}),
        marcadores AS (
            SELECT p.id_partido, p.id_equipo_local, p.id_equipo_visitante,
                   COALESCE(SUM(gc.id_equipo_gol = p.id_equipo_local), 0) AS goles_local,
                   COALESCE(SUM(gc.id_equipo_gol = p.id_equipo_visitante), 0) AS goles_visitante
            FROM partido p
            LEFT JOIN goles_creditados gc ON gc.id_partido = p.id_partido
            WHERE p.id_torneo = %s AND p.estado = 'jugado'
            GROUP BY p.id_partido, p.id_equipo_local, p.id_equipo_visitante
        )
        SELECT 'Victoria local' AS resultado, COALESCE(SUM(goles_local > goles_visitante), 0) AS cantidad
        FROM marcadores
        UNION ALL
        SELECT 'Empate', COALESCE(SUM(goles_local = goles_visitante), 0) FROM marcadores
        UNION ALL
        SELECT 'Victoria visitante', COALESCE(SUM(goles_local < goles_visitante), 0) FROM marcadores
    """
    with get_connection(user.rol) as conn:
        return fetch_all(conn, sql, (id_torneo,))


@router.get("/{id_torneo}/promedio-tarjetas-por-fecha")
def promedio_tarjetas_por_fecha(id_torneo: IdTorneo, user: AnyUser):
    with get_connection(user.rol) as conn:
        return fetch_all(
            conn,
            """
                SELECT p.numero_fecha,
                       COUNT(DISTINCT p.id_partido) AS partidos_jugados,
                       COUNT(t.id_tarjeta) AS tarjetas,
                       ROUND(COUNT(t.id_tarjeta) / NULLIF(COUNT(DISTINCT p.id_partido), 0), 2) AS promedio_tarjetas
                FROM partido p
                LEFT JOIN tarjeta t ON t.id_partido = p.id_partido
                WHERE p.id_torneo = %s AND p.estado = 'jugado'
                GROUP BY p.numero_fecha
                ORDER BY p.numero_fecha
            """,
            (id_torneo,),
        )


@router.get("/{id_torneo}/goles-por-facultad")
def goles_por_facultad(id_torneo: IdTorneo, user: AnyUser):
    with get_connection(user.rol) as conn:
        return fetch_all(
            conn,
            f"""
                WITH goles_creditados AS ({_GOLES_CREDITADOS})
                SELECT f.id_facultad, f.nombre AS facultad, COUNT(gc.id_partido) AS goles
                FROM partido p
                JOIN goles_creditados gc ON gc.id_partido = p.id_partido
                JOIN equipo e ON e.id_equipo = gc.id_equipo_gol
                JOIN facultad f ON f.id_facultad = e.id_facultad
                WHERE p.id_torneo = %s AND p.estado = 'jugado'
                GROUP BY f.id_facultad, f.nombre
                ORDER BY goles DESC, f.nombre
            """,
            (id_torneo,),
        )
