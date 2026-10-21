"""ABM de complejos y, anidadas, sus canchas (clave primaria compuesta: nombre_cancha + id_complejo)."""
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, status

from ..db import execute, fetch_all, fetch_one, get_connection
from ..deps import AdminUser, AnyUser
from ..schemas.complejo import (
    CanchaCreate, CanchaOut, CanchaPatch,
    ComplejoCreate, ComplejoOut, ComplejoPatch, Departamento,
)

router = APIRouter(prefix="/complejos", tags=["complejos"])

IdComplejo = Annotated[int, Path(gt=0)]
NombreCancha = Annotated[str, Path(min_length=1, max_length=100)]

_SELECT_COMPLEJO = "SELECT id_complejo, nombre, direccion, departamento FROM complejo"
_SELECT_CANCHA = "SELECT nombre_cancha, id_complejo, superficie, techada FROM cancha"


def _complejo(conn, id_complejo: int) -> dict | None:
    return fetch_one(conn, _SELECT_COMPLEJO + " WHERE id_complejo = %s", (id_complejo,))


def _cancha(conn, id_complejo: int, nombre: str) -> dict | None:
    return fetch_one(
        conn, _SELECT_CANCHA + " WHERE id_complejo = %s AND nombre_cancha = %s", (id_complejo, nombre)
    )


def _complejo_no_encontrado() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "Complejo no encontrado")


def _cancha_no_encontrada() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "Cancha no encontrada")


def _exigir_complejo(conn, id_complejo: int) -> None:
    if _complejo(conn, id_complejo) is None:
        raise _complejo_no_encontrado()


# ======================================== COMPLEJOS ========================================
@router.get("", response_model=list[ComplejoOut])
def listar(user: AnyUser, departamento: Departamento | None = None):
    sql, params = _SELECT_COMPLEJO, ()
    if departamento is not None:
        sql, params = sql + " WHERE departamento = %s", (departamento,)
    with get_connection(user.rol) as conn:
        return fetch_all(conn, sql + " ORDER BY nombre", params)


@router.get("/{id_complejo}", response_model=ComplejoOut)
def obtener(id_complejo: IdComplejo, user: AnyUser):
    with get_connection(user.rol) as conn:
        fila = _complejo(conn, id_complejo)
    if fila is None:
        raise _complejo_no_encontrado()
    return fila


@router.post("", response_model=ComplejoOut, status_code=status.HTTP_201_CREATED)
def crear(data: ComplejoCreate, user: AdminUser):
    with get_connection(user.rol) as conn:
        res = execute(
            conn,
            "INSERT INTO complejo (nombre, direccion, departamento) VALUES (%s, %s, %s)",
            (data.nombre, data.direccion, data.departamento),
        )
        return _complejo(conn, res.lastrowid)  # id autogenerado por AUTO_INCREMENT


@router.patch("/{id_complejo}", response_model=ComplejoOut)
def modificar(id_complejo: IdComplejo, data: ComplejoPatch, user: AdminUser):
    cambios = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    if not cambios:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se envió ningún campo para modificar")
    sets = ", ".join(f"{columna} = %s" for columna in cambios)  # columnas = campos del modelo, no del cliente
    with get_connection(user.rol) as conn:
        execute(conn, f"UPDATE complejo SET {sets} WHERE id_complejo = %s", (*cambios.values(), id_complejo))
        fila = _complejo(conn, id_complejo)
    if fila is None:
        raise _complejo_no_encontrado()
    return fila


@router.delete("/{id_complejo}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(id_complejo: IdComplejo, user: AdminUser):
    # Si tiene canchas, MySQL rechaza el DELETE (error 1451) y main.py lo devuelve como 409.
    with get_connection(user.rol) as conn:
        res = execute(conn, "DELETE FROM complejo WHERE id_complejo = %s", (id_complejo,))
    if res.rowcount == 0:
        raise _complejo_no_encontrado()


# ========================================= CANCHAS =========================================
@router.get("/{id_complejo}/canchas", response_model=list[CanchaOut], tags=["canchas"])
def listar_canchas(id_complejo: IdComplejo, user: AnyUser):
    with get_connection(user.rol) as conn:
        _exigir_complejo(conn, id_complejo)
        return fetch_all(conn, _SELECT_CANCHA + " WHERE id_complejo = %s ORDER BY nombre_cancha", (id_complejo,))


@router.get("/{id_complejo}/canchas/{nombre_cancha}", response_model=CanchaOut, tags=["canchas"])
def obtener_cancha(id_complejo: IdComplejo, nombre_cancha: NombreCancha, user: AnyUser):
    with get_connection(user.rol) as conn:
        fila = _cancha(conn, id_complejo, nombre_cancha)
    if fila is None:
        raise _cancha_no_encontrada()
    return fila


@router.post("/{id_complejo}/canchas", response_model=CanchaOut,
             status_code=status.HTTP_201_CREATED, tags=["canchas"])
def crear_cancha(id_complejo: IdComplejo, data: CanchaCreate, user: AdminUser):
    with get_connection(user.rol) as conn:
        _exigir_complejo(conn, id_complejo)
        execute(
            conn,
            "INSERT INTO cancha (nombre_cancha, id_complejo, superficie, techada) VALUES (%s, %s, %s, %s)",
            (data.nombre_cancha, id_complejo, data.superficie, data.techada),
        )
        return _cancha(conn, id_complejo, data.nombre_cancha)


@router.patch("/{id_complejo}/canchas/{nombre_cancha}", response_model=CanchaOut, tags=["canchas"])
def modificar_cancha(id_complejo: IdComplejo, nombre_cancha: NombreCancha,
                     data: CanchaPatch, user: AdminUser):
    # OJO: techada=False es un valor válido; por eso se filtra "is not None" y no "if v".
    cambios = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    if not cambios:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se envió ningún campo para modificar")
    sets = ", ".join(f"{columna} = %s" for columna in cambios)
    with get_connection(user.rol) as conn:
        execute(
            conn,
            f"UPDATE cancha SET {sets} WHERE id_complejo = %s AND nombre_cancha = %s",
            (*cambios.values(), id_complejo, nombre_cancha),
        )
        fila = _cancha(conn, id_complejo, nombre_cancha)
    if fila is None:
        raise _cancha_no_encontrada()
    return fila


@router.delete("/{id_complejo}/canchas/{nombre_cancha}",
               status_code=status.HTTP_204_NO_CONTENT, tags=["canchas"])
def eliminar_cancha(id_complejo: IdComplejo, nombre_cancha: NombreCancha, user: AdminUser):
    with get_connection(user.rol) as conn:
        res = execute(
            conn, "DELETE FROM cancha WHERE id_complejo = %s AND nombre_cancha = %s",
            (id_complejo, nombre_cancha),
        )
    if res.rowcount == 0:
        raise _cancha_no_encontrada()