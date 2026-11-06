"""ABM de turnos horarios."""
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, status

from ..db import execute, fetch_all, fetch_one, get_connection
from ..deps import AdminUser, AnyUser
from ..schemas.turno import TurnoCreate, TurnoOut, TurnoPatch

router = APIRouter(prefix="/turnos", tags=["turnos"])
IdTurno = Annotated[int, Path(gt=0)]
_SELECT = "SELECT id_turno, TIME_FORMAT(hora_inicio, '%%H:%%i:%%s') AS hora_inicio, TIME_FORMAT(hora_fin, '%%H:%%i:%%s') AS hora_fin FROM turno"


def _obtener(conn, id_turno: int) -> dict | None:
    return fetch_one(conn, _SELECT + " WHERE id_turno = %s", (id_turno,))


@router.get("", response_model=list[TurnoOut])
def listar(user: AnyUser):
    with get_connection(user.rol) as conn:
        return fetch_all(conn, _SELECT + " ORDER BY hora_inicio")


@router.get("/{id_turno}", response_model=TurnoOut)
def obtener(id_turno: IdTurno, user: AnyUser):
    with get_connection(user.rol) as conn:
        fila = _obtener(conn, id_turno)
    if fila is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Turno no encontrado")
    return fila


@router.post("", response_model=TurnoOut, status_code=status.HTTP_201_CREATED)
def crear(data: TurnoCreate, user: AdminUser):
    with get_connection(user.rol) as conn:
        res = execute(conn, "INSERT INTO turno (hora_inicio, hora_fin) VALUES (%s, %s)", (data.hora_inicio, data.hora_fin))
        return _obtener(conn, res.lastrowid)


@router.patch("/{id_turno}", response_model=TurnoOut)
def modificar(id_turno: IdTurno, data: TurnoPatch, user: AdminUser):
    cambios = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    if not cambios:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se envió ningún campo para modificar")
    with get_connection(user.rol) as conn:
        actual = _obtener(conn, id_turno)
        if actual is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Turno no encontrado")
        nuevo = {**actual, **cambios}
        if nuevo["hora_fin"] <= nuevo["hora_inicio"]:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "hora_fin debe ser posterior a hora_inicio")
        sets = ", ".join(f"{campo} = %s" for campo in cambios)
        execute(conn, f"UPDATE turno SET {sets} WHERE id_turno = %s", (*cambios.values(), id_turno))
        return _obtener(conn, id_turno)


@router.delete("/{id_turno}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(id_turno: IdTurno, user: AdminUser):
    with get_connection(user.rol) as conn:
        res = execute(conn, "DELETE FROM turno WHERE id_turno = %s", (id_turno,))
    if res.rowcount == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Turno no encontrado")
