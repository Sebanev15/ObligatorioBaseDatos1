from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from ..db import execute, fetch_all, fetch_one, get_connection
from ..deps import AdminUser, AnyUser
from ..schemas.jugador import JugadorCreate, JugadorOut, JugadorPatch, TipoJugador

router = APIRouter(prefix="/jugadores", tags=["jugadores"])

CI = Annotated[int, Path(ge=1_000_000, le=99_999_999, description="Cédula sin puntos ni guion")]

_SELECT = """
          SELECT j.ci, j.nombre, j.apellido, j.email, j.fecha_nacimiento,
                 j.id_facultad, f.nombre AS facultad, j.tipo
          FROM jugador j
                   JOIN facultad f ON f.id_facultad = j.id_facultad \
          """


def _obtener(conn, ci: int) -> dict | None:
    return fetch_one(conn, _SELECT + " WHERE j.ci = %s", (ci,))


def _no_encontrado() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "Jugador no encontrado")


@router.get("", response_model=list[JugadorOut])
def listar(
        user: AnyUser,
        id_facultad: int | None = None,
        tipo: TipoJugador | None = None,
        q: str | None = Query(None, max_length=60, description="Busca en nombre, apellido o CI"),
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
):
    # Las condiciones son texto fijo; los valores del usuario viajan SIEMPRE como parámetros (%s).
    condiciones: list[str] = []
    params: list = []
    if id_facultad is not None:
        condiciones.append("j.id_facultad = %s")
        params.append(id_facultad)
    if tipo is not None:
        condiciones.append("j.tipo = %s")
        params.append(tipo)
    if q:
        condiciones.append("(j.nombre LIKE %s OR j.apellido LIKE %s OR j.ci LIKE %s)")
        params += [f"%{q}%"] * 3

    where = (" WHERE " + " AND ".join(condiciones)) if condiciones else ""
    sql = _SELECT + where + " ORDER BY j.apellido, j.nombre LIMIT %s OFFSET %s"

    with get_connection(user.rol) as conn:
        return fetch_all(conn, sql, (*params, limit, offset))


@router.get("/{ci}", response_model=JugadorOut)
def obtener(ci: CI, user: AnyUser):
    with get_connection(user.rol) as conn:
        fila = _obtener(conn, ci)
    if fila is None:
        raise _no_encontrado()
    return fila


@router.post("", response_model=JugadorOut, status_code=status.HTTP_201_CREATED)
def crear(data: JugadorCreate, user: AdminUser):
    with get_connection(user.rol) as conn:
        execute(
            conn,
            """INSERT INTO jugador (ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (data.ci, data.nombre, data.apellido, data.email,
             data.fecha_nacimiento, data.id_facultad, data.tipo),
        )
        return _obtener(conn, data.ci)


@router.patch("/{ci}", response_model=JugadorOut)
def modificar(ci: CI, data: JugadorPatch, user: AdminUser):
    cambios = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    if not cambios:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se envió ningún campo para modificar")

    # Los nombres de columna salen de los campos del modelo Pydantic (extra="forbid"),
    # nunca del texto que manda el cliente, así que armar el SET así es seguro.
    sets = ", ".join(f"{columna} = %s" for columna in cambios)

    with get_connection(user.rol) as conn:
        execute(conn, f"UPDATE jugador SET {sets} WHERE ci = %s", (*cambios.values(), ci))
        # No se usa rowcount: MySQL devuelve 0 si el UPDATE no cambió ningún valor.
        fila = _obtener(conn, ci)
    if fila is None:
        raise _no_encontrado()
    return fila


@router.delete("/{ci}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(ci: CI, user: AdminUser):
    with get_connection(user.rol) as conn:
        res = execute(conn, "DELETE FROM jugador WHERE ci = %s", (ci,))
    if res.rowcount == 0:
        raise _no_encontrado()