"""Registro de tarjetas y recálculo transaccional de sanciones automáticas."""
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, status

from ..db import execute, fetch_all, fetch_one, get_connection
from ..deps import AnyUser, PlanilleroOrAdmin
from ..schemas.tarjeta import TarjetaCreate, TarjetaOut, TarjetaPatch
from ._partidos import exigir_partido_editable
from ._sanciones_automaticas import recalcular_sanciones_automaticas

router = APIRouter(prefix="/partidos/{id_partido}/tarjetas", tags=["tarjetas"])
IdPartido = Annotated[int, Path(gt=0)]
IdTarjeta = Annotated[int, Path(gt=0)]

_SELECT = """
    SELECT ta.id_tarjeta, ta.id_partido, ta.ci_jugador, CONCAT(j.nombre, ' ', j.apellido) AS jugador,
           pp.id_equipo, e.nombre AS equipo, ta.minuto, ta.color
    FROM tarjeta ta JOIN planilla_partido pp ON pp.id_partido = ta.id_partido AND pp.ci_jugador = ta.ci_jugador
    JOIN jugador j ON j.ci = ta.ci_jugador JOIN equipo e ON e.id_equipo = pp.id_equipo
"""


def _obtener(conn, id_partido: int, id_tarjeta: int) -> dict | None:
    return fetch_one(conn, _SELECT + " WHERE ta.id_partido = %s AND ta.id_tarjeta = %s", (id_partido, id_tarjeta))


@router.get("", response_model=list[TarjetaOut])
def listar(id_partido: IdPartido, user: AnyUser):
    with get_connection(user.rol) as conn:
        if fetch_one(conn, "SELECT 1 FROM partido WHERE id_partido = %s", (id_partido,)) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Partido no encontrado")
        return fetch_all(conn, _SELECT + " WHERE ta.id_partido = %s ORDER BY ta.minuto, ta.id_tarjeta", (id_partido,))


@router.post("", response_model=TarjetaOut, status_code=status.HTTP_201_CREATED)
def crear(id_partido: IdPartido, data: TarjetaCreate, user: PlanilleroOrAdmin):
    with get_connection("administrador") as conn:
        partido = exigir_partido_editable(conn, id_partido)
        if fetch_one(conn, "SELECT 1 FROM planilla_partido WHERE id_partido = %s AND ci_jugador = %s", (id_partido, data.ci_jugador)) is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Solo un jugador de la planilla puede recibir tarjetas")
        res = execute(conn, "INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES (%s, %s, %s, %s)", (id_partido, data.ci_jugador, data.minuto, data.color))
        recalcular_sanciones_automaticas(conn, partido["id_torneo"], data.ci_jugador)
        return _obtener(conn, id_partido, res.lastrowid)


@router.patch("/{id_tarjeta}", response_model=TarjetaOut)
def modificar(id_partido: IdPartido, id_tarjeta: IdTarjeta, data: TarjetaPatch, user: PlanilleroOrAdmin):
    cambios = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    if not cambios:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se envió ningún campo para modificar")
    with get_connection("administrador") as conn:
        partido = exigir_partido_editable(conn, id_partido)
        actual = _obtener(conn, id_partido, id_tarjeta)
        if actual is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarjeta no encontrada")
        sets = ", ".join(f"{campo} = %s" for campo in cambios)
        execute(conn, f"UPDATE tarjeta SET {sets} WHERE id_tarjeta = %s", (*cambios.values(), id_tarjeta))
        recalcular_sanciones_automaticas(conn, partido["id_torneo"], actual["ci_jugador"])
        return _obtener(conn, id_partido, id_tarjeta)


@router.delete("/{id_tarjeta}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(id_partido: IdPartido, id_tarjeta: IdTarjeta, user: PlanilleroOrAdmin):
    with get_connection("administrador") as conn:
        partido = exigir_partido_editable(conn, id_partido)
        actual = _obtener(conn, id_partido, id_tarjeta)
        if actual is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarjeta no encontrada")
        execute(conn, "DELETE FROM tarjeta WHERE id_tarjeta = %s", (id_tarjeta,))
        recalcular_sanciones_automaticas(conn, partido["id_torneo"], actual["ci_jugador"])
