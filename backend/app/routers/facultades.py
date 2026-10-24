from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from ..db import execute, fetch_all, fetch_one, get_connection
from ..deps import AdminUser, AnyUser
from ..schemas.facultad import FacultadCreate, FacultadOut, FacultadPut

router = APIRouter(prefix="/facultades", tags=["facultades"])

IdFacultad = Annotated[int, Path(gt=0)]

_SELECT = "SELECT id_facultad, nombre FROM facultad"


def _no_encontrada() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "Facultad no encontrada")


def _ya_existente(nombre: str) -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, f"Ya existe una facultad con el nombre {nombre}")


def _obtener_por_id(conn, id_facultad: int) -> dict | None:
    return fetch_one(conn, _SELECT + " WHERE id_facultad = %s", (id_facultad,))


def _obtener_por_nombre(conn, nombre: str) -> dict | None:
    return fetch_one(conn, _SELECT + " WHERE nombre = %s", (nombre,))


@router.get("", response_model=list[FacultadOut])
def listar(
    user: AnyUser,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    with get_connection(user.rol) as conn:
        return fetch_all(conn, _SELECT + " ORDER BY nombre LIMIT %s OFFSET %s", (limit, offset))


@router.get("/{id_facultad}", response_model=FacultadOut)
def obtener(id_facultad: IdFacultad, user: AnyUser):
    with get_connection(user.rol) as conn:
        fila = _obtener_por_id(conn, id_facultad)
    if fila is None:
        raise _no_encontrada()
    return fila


@router.post("", response_model=FacultadOut, status_code=status.HTTP_201_CREATED)
def crear(data: FacultadCreate, user: AdminUser):
    with get_connection(user.rol) as conn:
        if _obtener_por_nombre(conn, data.nombre) is not None:
            raise _ya_existente(data.nombre)
        res = execute(conn, "INSERT INTO facultad (nombre) VALUES (%s)", (data.nombre,))
        return _obtener_por_id(conn, res.lastrowid)


@router.put("/{id_facultad}", response_model=FacultadOut)
def actualizar(id_facultad: IdFacultad, data: FacultadPut, user: AdminUser):
    with get_connection(user.rol) as conn:
        if _obtener_por_id(conn, id_facultad) is None:
            raise _no_encontrada()
        # Otro registro con ese nombre = conflicto. Si es el mismo registro, no pasa nada.
        otra = _obtener_por_nombre(conn, data.nombre)
        if otra is not None and otra["id_facultad"] != id_facultad:
            raise _ya_existente(data.nombre)
        execute(conn, "UPDATE facultad SET nombre = %s WHERE id_facultad = %s", (data.nombre, id_facultad))
        return _obtener_por_id(conn, id_facultad)



@router.delete("/{id_facultad}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(id_facultad: IdFacultad, user: AdminUser):
    with get_connection(user.rol) as conn:
        fila = _obtener_por_id(conn, id)
        if fila is None:
            raise _no_encontrado()
        execute(conn, f"DELETE FROM facultad WHERE id_facultad = %s", (id_facultad,))



