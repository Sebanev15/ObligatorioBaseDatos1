
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from ..db import execute, fetch_all, fetch_one, get_connection
from ..deps import AdminUser, AnyUser
from ..schemas.torneo import TorneoCreate, TorneoOut, TorneoPatch

router = APIRouter(prefix="/torneos", tags=["torneos"])

IdTorneo = Annotated[int, Path(gt=0)]

_SELECT = """
    SELECT id_torneo, nombre, anio, semestre,
           fecha_inicio, fecha_fin, estado
    FROM torneo
"""


def _no_encontrado() -> HTTPException:
    return HTTPException(
        status.HTTP_404_NOT_FOUND,
        "Torneo no encontrado",
    )


def _obtener(conn, id_torneo: int) -> dict | None:
    return fetch_one(
        conn,
        _SELECT + " WHERE id_torneo = %s",
        (id_torneo,),
    )


@router.get("", response_model=list[TorneoOut])
def listar(
    user: AnyUser,
    anio: int | None = Query(default=None, ge=1, le=9999),
    semestre: int | None = Query(default=None, ge=1, le=2),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    condiciones = []
    params = []

    if anio is not None:
        condiciones.append("anio = %s")
        params.append(anio)

    if semestre is not None:
        condiciones.append("semestre = %s")
        params.append(semestre)

    where = (
        " WHERE " + " AND ".join(condiciones)
        if condiciones else ""
    )

    sql = _SELECT + where + """
        ORDER BY anio DESC, semestre DESC, nombre
        LIMIT %s OFFSET %s
    """

    with get_connection(user.rol) as conn:
        return fetch_all(conn, sql, (*params, limit, offset))


@router.get("/{id_torneo}", response_model=TorneoOut)
def obtener(id_torneo: IdTorneo, user: AnyUser):
    with get_connection(user.rol) as conn:
        fila = _obtener(conn, id_torneo)

    if fila is None:
        raise _no_encontrado()

    return fila


@router.post(
    "",
    response_model=TorneoOut,
    status_code=status.HTTP_201_CREATED,
)
def crear(data: TorneoCreate, user: AdminUser):
    with get_connection(user.rol) as conn:
        res = execute(
            conn,
            """
                INSERT INTO torneo
                    (nombre, anio, semestre, fecha_inicio,
                     fecha_fin, estado)
                VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                data.nombre,
                data.anio,
                data.semestre,
                data.fecha_inicio,
                data.fecha_fin,
                data.estado,
            ),
        )

        return _obtener(conn, res.lastrowid)


@router.patch("/{id_torneo}", response_model=TorneoOut)
def modificar(
    id_torneo: IdTorneo,
    data: TorneoPatch,
    user: AdminUser,
):
    cambios = data.model_dump(exclude_unset=True, exclude_none=True)

    if not cambios:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "No se envió ningún campo válido para modificar",
        )

    with get_connection(user.rol) as conn:
        fila = _obtener(conn, id_torneo)

        if fila is None:
            raise _no_encontrado()

        # Se valida la combinación de fechas nuevas y existentes.
        fecha_inicio = cambios.get("fecha_inicio", fila["fecha_inicio"])
        fecha_fin = cambios.get("fecha_fin", fila["fecha_fin"])

        if fecha_fin < fecha_inicio:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "La fecha de fin debe ser posterior o igual a la fecha de inicio",
            )

        # Los nombres de columna proceden exclusivamente del schema.
        sets = ", ".join(f"{columna} = %s" for columna in cambios)

        execute(
            conn,
            f"UPDATE torneo SET {sets} WHERE id_torneo = %s",
            (*cambios.values(), id_torneo),
        )

        return _obtener(conn, id_torneo)


@router.delete(
    "/{id_torneo}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def eliminar(id_torneo: IdTorneo, user: AdminUser):
    with get_connection(user.rol) as conn:
        if _obtener(conn, id_torneo) is None:
            raise _no_encontrado()

        execute(
            conn,
            "DELETE FROM torneo WHERE id_torneo = %s",
            (id_torneo,),
        )
