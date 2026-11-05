from collections.abc import Sequence
from typing import Any

from fastapi import HTTPException, status

from ..db import execute, fetch_all


def _exigir_sin_partidos_jugados(
    conn: Any,
    condicion: str,
    parametros: Sequence[Any],
    entidad: str,
) -> None:
    partido = fetch_all(
        conn,
        f"""SELECT p.id_partido FROM partido p
            WHERE ({condicion})
              AND (
                  p.estado = 'jugado'
                  OR EXISTS (SELECT 1 FROM gol g WHERE g.id_partido = p.id_partido)
                  OR EXISTS (SELECT 1 FROM tarjeta t WHERE t.id_partido = p.id_partido)
              )
            LIMIT 1""",
        parametros,
    )
    if partido:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"No se puede eliminar {entidad}: tiene datos de partidos jugados y se perdería su historial.",
        )


def _eliminar_partidos(conn: Any, condicion: str, parametros: Sequence[Any]) -> None:
    partidos = fetch_all(conn, f"SELECT id_partido FROM partido WHERE {condicion}", parametros)
    for partido in partidos:
        id_partido = partido["id_partido"]
        execute(conn, "DELETE FROM gol WHERE id_partido = %s", (id_partido,))
        execute(conn, "DELETE FROM tarjeta WHERE id_partido = %s", (id_partido,))
        execute(conn, "DELETE FROM planilla_partido WHERE id_partido = %s", (id_partido,))
        execute(conn, "DELETE FROM partido WHERE id_partido = %s", (id_partido,))


def eliminar_partidos_de_equipo(conn: Any, id_equipo: int) -> None:
    condicion = "id_equipo_local = %s OR id_equipo_visitante = %s"
    parametros = (id_equipo, id_equipo)
    _exigir_sin_partidos_jugados(conn, condicion, parametros, "el equipo")
    _eliminar_partidos(conn, condicion, parametros)


def eliminar_partidos_de_torneo(conn: Any, id_torneo: int) -> None:
    condicion = "id_torneo = %s"
    parametros = (id_torneo,)
    _exigir_sin_partidos_jugados(conn, condicion, parametros, "el torneo")
    _eliminar_partidos(conn, condicion, parametros)


def eliminar_partidos_de_complejo(conn: Any, id_complejo: int) -> None:
    condicion = "id_complejo = %s"
    parametros = (id_complejo,)
    _exigir_sin_partidos_jugados(conn, condicion, parametros, "el complejo")
    _eliminar_partidos(conn, condicion, parametros)


def eliminar_partidos_de_cancha(conn: Any, id_complejo: int, nombre_cancha: str) -> None:
    condicion = "id_complejo = %s AND nombre_cancha = %s"
    parametros = (id_complejo, nombre_cancha)
    _exigir_sin_partidos_jugados(conn, condicion, parametros, "la cancha")
    _eliminar_partidos(conn, condicion, parametros)


def eliminar_participacion(conn: Any, id_equipo: int, ci: int) -> None:
    participacion_jugada = fetch_all(
        conn,
        """SELECT pp.id_partido
           FROM planilla_partido pp
           JOIN partido p ON p.id_partido = pp.id_partido
           WHERE pp.id_equipo = %s AND pp.ci_jugador = %s
             AND (
                 p.estado = 'jugado'
                 OR EXISTS (
                     SELECT 1 FROM gol g
                     WHERE g.id_partido = p.id_partido AND g.ci_jugador = pp.ci_jugador
                 )
                 OR EXISTS (
                     SELECT 1 FROM tarjeta t
                     WHERE t.id_partido = p.id_partido AND t.ci_jugador = pp.ci_jugador
                 )
             )
           LIMIT 1""",
        (id_equipo, ci),
    )
    if participacion_jugada:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "No se puede quitar al jugador del plantel: figura en partidos jugados y se perdería su historial.",
        )

    sancion = fetch_all(
        conn,
        """SELECT s.id_sancion
           FROM sancion_jugador s
           JOIN equipo e ON e.id_torneo = s.id_torneo
           WHERE e.id_equipo = %s AND s.ci_jugador = %s
           LIMIT 1""",
        (id_equipo, ci),
    )
    if sancion:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "No se puede quitar al jugador del plantel mientras tenga sanciones en este torneo.",
        )

    parametros = (id_equipo, ci)
    execute(
        conn,
        """DELETE FROM gol WHERE ci_jugador = %s
           AND id_partido IN (
               SELECT id_partido FROM planilla_partido
               WHERE id_equipo = %s AND ci_jugador = %s
           )""",
        (ci, *parametros),
    )
    execute(
        conn,
        """DELETE FROM tarjeta WHERE ci_jugador = %s
           AND id_partido IN (
               SELECT id_partido FROM planilla_partido
               WHERE id_equipo = %s AND ci_jugador = %s
           )""",
        (ci, *parametros),
    )
    execute(
        conn,
        "DELETE FROM planilla_partido WHERE id_equipo = %s AND ci_jugador = %s",
        parametros,
    )


def eliminar_equipo(conn: Any, id_equipo: int) -> None:
    eliminar_partidos_de_equipo(conn, id_equipo)
    sancion = fetch_all(
        conn,
        """SELECT s.id_sancion
           FROM sancion_jugador s
           JOIN equipo_jugador_torneo ejt
             ON ejt.ci_jugador = s.ci_jugador AND ejt.id_torneo = s.id_torneo
           WHERE ejt.id_equipo = %s
           LIMIT 1""",
        (id_equipo,),
    )
    if sancion:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "No se puede eliminar el equipo mientras sus jugadores tengan sanciones en este torneo.",
        )
    execute(conn, "UPDATE equipo SET ci_capitan = NULL WHERE id_equipo = %s", (id_equipo,))
    execute(conn, "DELETE FROM equipo_jugador_torneo WHERE id_equipo = %s", (id_equipo,))
    execute(conn, "DELETE FROM equipo WHERE id_equipo = %s", (id_equipo,))


def eliminar_jugador(conn: Any, ci: int) -> None:
    partido_jugado = fetch_all(
        conn,
        """SELECT p.id_partido
           FROM planilla_partido pp
           JOIN partido p ON p.id_partido = pp.id_partido
           WHERE pp.ci_jugador = %s
             AND (
                 p.estado = 'jugado'
                 OR EXISTS (
                     SELECT 1 FROM gol g
                     WHERE g.id_partido = p.id_partido AND g.ci_jugador = pp.ci_jugador
                 )
                 OR EXISTS (
                     SELECT 1 FROM tarjeta t
                     WHERE t.id_partido = p.id_partido AND t.ci_jugador = pp.ci_jugador
                 )
             )
           LIMIT 1""",
        (ci,),
    )
    if partido_jugado:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "No se puede eliminar el jugador: figura en partidos jugados y se perdería su historial.",
        )
    sancion = fetch_all(conn, "SELECT id_sancion FROM sancion_jugador WHERE ci_jugador = %s LIMIT 1", (ci,))
    if sancion:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "No se puede eliminar el jugador mientras tenga sanciones registradas.",
        )

    execute(
        conn,
        """DELETE FROM gol WHERE ci_jugador = %s
           AND id_partido IN (SELECT id_partido FROM partido WHERE estado <> 'jugado')""",
        (ci,),
    )
    execute(
        conn,
        """DELETE FROM tarjeta WHERE ci_jugador = %s
           AND id_partido IN (SELECT id_partido FROM partido WHERE estado <> 'jugado')""",
        (ci,),
    )
    execute(
        conn,
        """DELETE FROM planilla_partido WHERE ci_jugador = %s
           AND id_partido IN (SELECT id_partido FROM partido WHERE estado <> 'jugado')""",
        (ci,),
    )
    execute(conn, "UPDATE equipo SET ci_capitan = NULL WHERE ci_capitan = %s", (ci,))
    execute(conn, "DELETE FROM equipo_jugador_torneo WHERE ci_jugador = %s", (ci,))
    execute(conn, "DELETE FROM jugador WHERE ci = %s", (ci,))
