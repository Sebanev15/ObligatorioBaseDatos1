"""Registro de goles de un partido."""
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, status

from ..db import execute, fetch_all, fetch_one, get_connection
from ..deps import AnyUser, PlanilleroOrAdmin
from ..schemas.gol import GolCreate, GolOut, GolPatch
from ._partidos import exigir_partido_editable

router = APIRouter(prefix="/partidos/{id_partido}/goles", tags=["goles"])
IdPartido = Annotated[int, Path(gt=0)]
IdGol = Annotated[int, Path(gt=0)]

_SELECT = """
    SELECT g.id_gol, g.id_partido, g.ci_jugador, CONCAT(j.nombre, ' ', j.apellido) AS jugador,
           pp.id_equipo, e.nombre AS equipo, g.minuto, g.autogol
    FROM gol g JOIN planilla_partido pp ON pp.id_partido = g.id_partido AND pp.ci_jugador = g.ci_jugador
    JOIN jugador j ON j.ci = g.ci_jugador JOIN equipo e ON e.id_equipo = pp.id_equipo
"""


def _obtener(conn, id_partido: int, id_gol: int) -> dict | None:
    return fetch_one(conn, _SELECT + " WHERE g.id_partido = %s AND g.id_gol = %s", (id_partido, id_gol))


@router.get("", response_model=list[GolOut])
def listar(id_partido: IdPartido, user: AnyUser):
    with get_connection(user.rol) as conn:
        if fetch_one(conn, "SELECT 1 FROM partido WHERE id_partido = %s", (id_partido,)) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Partido no encontrado")
        return fetch_all(conn, _SELECT + " WHERE g.id_partido = %s ORDER BY g.minuto, g.id_gol", (id_partido,))


@router.post("", response_model=GolOut, status_code=status.HTTP_201_CREATED)
def crear(id_partido: IdPartido, data: GolCreate, user: PlanilleroOrAdmin):
    with get_connection(user.rol) as conn:
        exigir_partido_editable(conn, id_partido)
        if fetch_one(conn, "SELECT 1 FROM planilla_partido WHERE id_partido = %s AND ci_jugador = %s", (id_partido, data.ci_jugador)) is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Solo un jugador de la planilla puede convertir goles")
        res = execute(conn, "INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES (%s, %s, %s, %s)", (id_partido, data.ci_jugador, data.minuto, data.autogol))
        return _obtener(conn, id_partido, res.lastrowid)


@router.patch("/{id_gol}", response_model=GolOut)
def modificar(id_partido: IdPartido, id_gol: IdGol, data: GolPatch, user: PlanilleroOrAdmin):
    cambios = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    if not cambios:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se envió ningún campo para modificar")
    with get_connection(user.rol) as conn:
        exigir_partido_editable(conn, id_partido)
        if _obtener(conn, id_partido, id_gol) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Gol no encontrado")
        sets = ", ".join(f"{campo} = %s" for campo in cambios)
        execute(conn, f"UPDATE gol SET {sets} WHERE id_gol = %s", (*cambios.values(), id_gol))
        return _obtener(conn, id_partido, id_gol)


@router.delete("/{id_gol}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(id_partido: IdPartido, id_gol: IdGol, user: PlanilleroOrAdmin):
    with get_connection(user.rol) as conn:
        exigir_partido_editable(conn, id_partido)
        if _obtener(conn, id_partido, id_gol) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Gol no encontrado")
        execute(conn, "DELETE FROM gol WHERE id_gol = %s", (id_gol,))
