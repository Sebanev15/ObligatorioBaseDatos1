"""Programación y seguimiento de partidos."""
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from ..db import execute, fetch_all, fetch_one, get_connection
from ..deps import AdminUser, AnyUser
from ..schemas.partido import EstadoPartido, PartidoCreate, PartidoOut, PartidoPatch
from ._partidos import exigir_horario_pasado, partido as buscar_partido
from ._sanciones_automaticas import recalcular_sanciones_automaticas

router = APIRouter(prefix="/partidos", tags=["partidos"])
IdPartido = Annotated[int, Path(gt=0)]

_SELECT = """
    SELECT p.id_partido, p.id_torneo, tr.nombre AS torneo, p.numero_fecha,
           p.id_equipo_local, el.nombre AS equipo_local,
           p.id_equipo_visitante, ev.nombre AS equipo_visitante,
           p.dia, p.id_turno, TIME_FORMAT(t.hora_inicio, '%%H:%%i:%%s') AS hora_inicio,
           TIME_FORMAT(t.hora_fin, '%%H:%%i:%%s') AS hora_fin,
           p.nombre_cancha, p.id_complejo, c.nombre AS complejo, p.estado,
           COALESCE(SUM(CASE WHEN (g.autogol = 0 AND pp.id_equipo = p.id_equipo_local)
                             OR (g.autogol = 1 AND pp.id_equipo = p.id_equipo_visitante) THEN 1 ELSE 0 END), 0) AS goles_local,
           COALESCE(SUM(CASE WHEN (g.autogol = 0 AND pp.id_equipo = p.id_equipo_visitante)
                             OR (g.autogol = 1 AND pp.id_equipo = p.id_equipo_local) THEN 1 ELSE 0 END), 0) AS goles_visitante
    FROM partido p
    JOIN torneo tr ON tr.id_torneo = p.id_torneo
    JOIN equipo el ON el.id_equipo = p.id_equipo_local
    JOIN equipo ev ON ev.id_equipo = p.id_equipo_visitante
    JOIN turno t ON t.id_turno = p.id_turno
    JOIN complejo c ON c.id_complejo = p.id_complejo
    LEFT JOIN gol g ON g.id_partido = p.id_partido
    LEFT JOIN planilla_partido pp ON pp.id_partido = g.id_partido AND pp.ci_jugador = g.ci_jugador
"""
_GROUP = " GROUP BY p.id_partido, tr.nombre, el.nombre, ev.nombre, t.hora_inicio, t.hora_fin, c.nombre"


def _obtener(conn, id_partido: int) -> dict | None:
    return fetch_one(conn, _SELECT + " WHERE p.id_partido = %s" + _GROUP, (id_partido,))


def _validar_programacion(conn, datos: dict, id_partido: int | None = None) -> None:
    if datos["id_equipo_local"] == datos["id_equipo_visitante"]:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Un equipo no puede jugar contra sí mismo")
    torneo = fetch_one(conn, "SELECT estado FROM torneo WHERE id_torneo = %s", (datos["id_torneo"],))
    if torneo is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "El torneo indicado no existe")
    if torneo["estado"] == "finalizado":
        raise HTTPException(status.HTTP_409_CONFLICT, "No se pueden programar partidos en un torneo finalizado")
    if fetch_one(conn, "SELECT 1 FROM turno WHERE id_turno = %s", (datos["id_turno"],)) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "El turno indicado no existe")
    if fetch_one(conn, "SELECT 1 FROM cancha WHERE nombre_cancha = %s AND id_complejo = %s", (datos["nombre_cancha"], datos["id_complejo"])) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "La cancha indicada no existe en ese complejo")
    equipos = fetch_all(conn, """SELECT e.id_equipo, COUNT(ejt.ci_jugador) AS jugadores
                                FROM equipo e LEFT JOIN equipo_jugador_torneo ejt ON ejt.id_equipo = e.id_equipo
                                WHERE e.id_torneo = %s AND e.id_equipo IN (%s, %s)
                                GROUP BY e.id_equipo""", (datos["id_torneo"], datos["id_equipo_local"], datos["id_equipo_visitante"]))
    if len(equipos) != 2:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Los dos equipos deben pertenecer al torneo")
    if any(e["jugadores"] < 5 for e in equipos):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ambos equipos deben tener al menos 5 jugadores")
    excluir = " AND p.id_partido <> %s" if id_partido is not None else ""
    extra = (id_partido,) if id_partido is not None else ()
    repetido = fetch_one(conn, """SELECT 1 FROM partido p WHERE p.id_torneo = %s AND p.estado <> 'cancelado'
        AND ((p.id_equipo_local = %s AND p.id_equipo_visitante = %s) OR (p.id_equipo_local = %s AND p.id_equipo_visitante = %s))""" + excluir,
        (datos["id_torneo"], datos["id_equipo_local"], datos["id_equipo_visitante"], datos["id_equipo_visitante"], datos["id_equipo_local"], *extra))
    if repetido:
        raise HTTPException(status.HTTP_409_CONFLICT, "Los equipos ya tienen un partido no cancelado en esta edición")
    misma_fecha = fetch_one(conn, """SELECT 1 FROM partido p WHERE p.id_torneo = %s AND p.numero_fecha = %s AND p.estado <> 'cancelado'
        AND (p.id_equipo_local IN (%s, %s) OR p.id_equipo_visitante IN (%s, %s))""" + excluir,
        (datos["id_torneo"], datos["numero_fecha"], datos["id_equipo_local"], datos["id_equipo_visitante"], datos["id_equipo_local"], datos["id_equipo_visitante"], *extra))
    if misma_fecha:
        raise HTTPException(status.HTTP_409_CONFLICT, "Un equipo no puede jugar más de un partido en la misma fecha")


@router.get("", response_model=list[PartidoOut])
def listar(user: AnyUser, id_torneo: int | None = None, numero_fecha: int | None = Query(None, gt=0), estado: EstadoPartido | None = None):
    condiciones, params = [], []
    for columna, valor in (("p.id_torneo", id_torneo), ("p.numero_fecha", numero_fecha), ("p.estado", estado)):
        if valor is not None:
            condiciones.append(f"{columna} = %s")
            params.append(valor)
    where = " WHERE " + " AND ".join(condiciones) if condiciones else ""
    with get_connection(user.rol) as conn:
        return fetch_all(conn, _SELECT + where + _GROUP + " ORDER BY p.dia, t.hora_inicio, p.id_partido", params)


@router.get("/{id_partido}", response_model=PartidoOut)
def obtener(id_partido: IdPartido, user: AnyUser):
    with get_connection(user.rol) as conn:
        fila = _obtener(conn, id_partido)
    if fila is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Partido no encontrado")
    return fila


@router.post("", response_model=PartidoOut, status_code=status.HTTP_201_CREATED)
def crear(data: PartidoCreate, user: AdminUser):
    datos = data.model_dump()
    with get_connection(user.rol) as conn:
        _validar_programacion(conn, datos)
        res = execute(conn, """INSERT INTO partido (id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante, dia, id_turno, nombre_cancha, id_complejo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", tuple(datos.values()))
        return _obtener(conn, res.lastrowid)


@router.patch("/{id_partido}", response_model=PartidoOut)
def modificar(id_partido: IdPartido, data: PartidoPatch, user: AdminUser):
    cambios = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    if not cambios:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se envió ningún campo para modificar")
    if "estado" in cambios:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El estado se modifica en /partidos/{id_partido}/estado")
    with get_connection(user.rol) as conn:
        actual = buscar_partido(conn, id_partido)
        if actual is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Partido no encontrado")
        if actual["estado"] == "jugado":
            raise HTTPException(status.HTTP_409_CONFLICT, "Un partido jugado no se puede reprogramar ni cancelar")
        nuevo = {**actual, **cambios}
        _validar_programacion(conn, nuevo, id_partido)
        sets = ", ".join(f"{campo} = %s" for campo in cambios)
        execute(conn, f"UPDATE partido SET {sets} WHERE id_partido = %s", (*cambios.values(), id_partido))
        return _obtener(conn, id_partido)


@router.patch("/{id_partido}/estado", response_model=PartidoOut)
def cambiar_estado(id_partido: IdPartido, data: PartidoPatch, user: AdminUser):
    if data.estado is None or len(data.model_dump(exclude_unset=True)) != 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Solo se debe enviar el estado del partido")
    with get_connection(user.rol) as conn:
        actual = buscar_partido(conn, id_partido)
        if actual is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Partido no encontrado")
        if data.estado == "jugado":
            exigir_horario_pasado(actual)
        if actual["estado"] == "jugado" and data.estado != "jugado":
            raise HTTPException(status.HTTP_409_CONFLICT, "Un partido jugado no puede cambiar de estado")
        execute(conn, "UPDATE partido SET estado = %s WHERE id_partido = %s", (data.estado, id_partido))
        if data.estado == "jugado":
            jugadores_con_tarjetas = fetch_all(
                conn,
                "SELECT DISTINCT ci_jugador FROM tarjeta WHERE id_partido = %s",
                (id_partido,),
            )
            for jugador in jugadores_con_tarjetas:
                recalcular_sanciones_automaticas(
                    conn,
                    actual["id_torneo"],
                    jugador["ci_jugador"],
                )
        return _obtener(conn, id_partido)


@router.delete("/{id_partido}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(id_partido: IdPartido, user: AdminUser):
    with get_connection(user.rol) as conn:
        actual = buscar_partido(conn, id_partido)
        if actual is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Partido no encontrado")
        if actual["estado"] == "jugado":
            raise HTTPException(status.HTTP_409_CONFLICT, "Un partido jugado no puede eliminarse")
        execute(conn, "DELETE FROM partido WHERE id_partido = %s", (id_partido,))
