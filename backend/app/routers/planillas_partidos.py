"""Participantes de la planilla de cada partido."""
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, status

from ..db import execute, fetch_all, fetch_one, get_connection
from ..deps import AnyUser, PlanilleroOrAdmin
from ..schemas.planilla_partido import PlanillaPartidoCreate, PlanillaPartidoOut
from ._partidos import exigir_partido_editable

router = APIRouter(prefix="/partidos/{id_partido}/planilla", tags=["planillas"])
IdPartido = Annotated[int, Path(gt=0)]
CI = Annotated[int, Path(ge=1_000_000, le=99_999_999)]

_SELECT = """
    SELECT pp.id_partido, pp.ci_jugador, pp.id_equipo,
           CONCAT(j.nombre, ' ', j.apellido) AS jugador, e.nombre AS equipo
    FROM planilla_partido pp
    JOIN jugador j ON j.ci = pp.ci_jugador
    JOIN equipo e ON e.id_equipo = pp.id_equipo
"""


def _obtener(conn, id_partido: int, ci: int) -> dict | None:
    return fetch_one(conn, _SELECT + " WHERE pp.id_partido = %s AND pp.ci_jugador = %s", (id_partido, ci))


@router.get("", response_model=list[PlanillaPartidoOut])
def listar(id_partido: IdPartido, user: AnyUser):
    with get_connection(user.rol) as conn:
        if fetch_one(conn, "SELECT 1 FROM partido WHERE id_partido = %s", (id_partido,)) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Partido no encontrado")
        return fetch_all(conn, _SELECT + " WHERE pp.id_partido = %s ORDER BY e.nombre, j.apellido, j.nombre", (id_partido,))


@router.post("", response_model=PlanillaPartidoOut, status_code=status.HTTP_201_CREATED)
def agregar(id_partido: IdPartido, data: PlanillaPartidoCreate, user: PlanilleroOrAdmin):
    with get_connection(user.rol) as conn:
        partido = exigir_partido_editable(conn, id_partido)
        if data.id_equipo not in (partido["id_equipo_local"], partido["id_equipo_visitante"]):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "El equipo no participa de este partido")
        if fetch_one(conn, """SELECT 1 FROM equipo_jugador_torneo WHERE id_equipo = %s AND ci_jugador = %s AND id_torneo = %s""", (data.id_equipo, data.ci_jugador, partido["id_torneo"])) is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "El jugador no integra el plantel de ese equipo")
        suspendido = fetch_one(conn, """SELECT 1 FROM sancion_jugador
            WHERE ci_jugador = %s AND id_torneo = %s
              AND %s BETWEEN numero_fecha_inicio AND numero_fecha_inicio + cantidad_fechas - 1""", (data.ci_jugador, partido["id_torneo"], partido["numero_fecha"]))
        if suspendido:
            raise HTTPException(status.HTTP_409_CONFLICT, "El jugador está suspendido para esta fecha")
        execute(conn, "INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES (%s, %s, %s)", (id_partido, data.ci_jugador, data.id_equipo))
        return _obtener(conn, id_partido, data.ci_jugador)


@router.delete("/{ci_jugador}", status_code=status.HTTP_204_NO_CONTENT)
def quitar(id_partido: IdPartido, ci_jugador: CI, user: PlanilleroOrAdmin):
    with get_connection(user.rol) as conn:
        exigir_partido_editable(conn, id_partido)
        if _obtener(conn, id_partido, ci_jugador) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El jugador no figura en la planilla")
        # Si ya tiene goles o tarjetas, MySQL rechaza el DELETE por FK y main.py devuelve 409.
        execute(conn, "DELETE FROM planilla_partido WHERE id_partido = %s AND ci_jugador = %s", (id_partido, ci_jugador))
