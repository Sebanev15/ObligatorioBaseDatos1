
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from ..db import execute, fetch_all, fetch_one, get_connection
from ..deps import AdminUser, AnyUser
from ..schemas.equipo import EquipoCreate, EquipoOut, EquipoPatch

router = APIRouter(prefix="/equipos", tags=["equipos"])

IdEquipo = Annotated[int, Path(gt=0)]

_SELECT = """
    SELECT id_equipo, nombre, id_torneo, id_facultad, ci_capitan
    FROM equipo
"""


def _obtener(conn, id_equipo: int) -> dict | None:
    return fetch_one(
        conn,
        _SELECT + " WHERE id_equipo = %s",
        (id_equipo,),
    )


def _obtener_por_nombre(
    conn,
    nombre: str,
    id_torneo: int,
) -> dict | None:
    return fetch_one(
        conn,
        _SELECT + """
            WHERE nombre = %s AND id_torneo = %s
        """,
        (nombre, id_torneo),
    )


def _no_encontrado() -> HTTPException:
    return HTTPException(
        status.HTTP_404_NOT_FOUND,
        "Equipo no encontrado",
    )


def _conflicto_nombre() -> HTTPException:
    return HTTPException(
        status.HTTP_409_CONFLICT,
        "Ya existe un equipo con ese nombre en el torneo",
    )


def _validar_capitan(
    conn,
    id_equipo: int,
    id_torneo: int,
    ci_capitan: int,
) -> bool:
    fila = fetch_one(
        conn,
        """
            SELECT id_equipo
            FROM equipo_jugador_torneo
            WHERE id_equipo = %s
              AND ci_jugador = %s
              AND id_torneo = %s
        """,
        (id_equipo, ci_capitan, id_torneo),
    )
    return fila is not None


@router.get("", response_model=list[EquipoOut])
def listar(
    user: AnyUser,
    id_torneo: int | None = Query(default=None, gt=0),
    id_facultad: int | None = Query(default=None, gt=0),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    condiciones = []
    params = []

    if id_torneo is not None:
        condiciones.append("id_torneo = %s")
        params.append(id_torneo)

    if id_facultad is not None:
        condiciones.append("id_facultad = %s")
        params.append(id_facultad)

    where = (
        " WHERE " + " AND ".join(condiciones)
        if condiciones else ""
    )

    sql = _SELECT + where + """
        ORDER BY nombre
        LIMIT %s OFFSET %s
    """

    with get_connection(user.rol) as conn:
        return fetch_all(conn, sql, (*params, limit, offset))


@router.get("/{id_equipo}", response_model=EquipoOut)
def obtener(id_equipo: IdEquipo, user: AnyUser):
    with get_connection(user.rol) as conn:
        fila = _obtener(conn, id_equipo)

    if fila is None:
        raise _no_encontrado()

    return fila


@router.post(
    "",
    response_model=EquipoOut,
    status_code=status.HTTP_201_CREATED,
)
def crear(data: EquipoCreate, user: AdminUser):
    with get_connection(user.rol) as conn:
        torneo = fetch_one(
            conn,
            "SELECT id_torneo FROM torneo WHERE id_torneo = %s",
            (data.id_torneo,),
        )
        if torneo is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "Torneo no encontrado",
            )

        facultad = fetch_one(
            conn,
            "SELECT id_facultad FROM facultad WHERE id_facultad = %s",
            (data.id_facultad,),
        )
        if facultad is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "Facultad no encontrada",
            )

        if _obtener_por_nombre(
            conn, data.nombre, data.id_torneo
        ) is not None:
            raise _conflicto_nombre()

        res = execute(
            conn,
            """
                INSERT INTO equipo
                    (nombre, id_torneo, id_facultad, ci_capitan)
                VALUES (%s, %s, %s, NULL)
            """,
            (data.nombre, data.id_torneo, data.id_facultad),
        )

        return _obtener(conn, res.lastrowid)


@router.patch("/{id_equipo}", response_model=EquipoOut)
def modificar(
    id_equipo: IdEquipo,
    data: EquipoPatch,
    user: AdminUser,
):
    enviados = data.model_dump(exclude_unset=True)

    # Los campos normales ignoran null; ci_capitan sí admite null.
    cambios = {
        k: v
        for k, v in enviados.items()
        if v is not None or k == "ci_capitan"
    }

    if not cambios:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "No se envió ningún campo válido para modificar",
        )

    with get_connection(user.rol) as conn:
        equipo = _obtener(conn, id_equipo)

        if equipo is None:
            raise _no_encontrado()

        id_torneo = equipo["id_torneo"]

        if "id_facultad" in cambios:
            facultad = fetch_one(
                conn,
                "SELECT id_facultad FROM facultad WHERE id_facultad = %s",
                (cambios["id_facultad"],),
            )
            if facultad is None:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND,
                    "Facultad no encontrada",
                )

        nombre = cambios.get("nombre", equipo["nombre"])

        otro = _obtener_por_nombre(conn, nombre, id_torneo)
        if otro is not None and otro["id_equipo"] != id_equipo:
            raise _conflicto_nombre()

        if "ci_capitan" in cambios and cambios["ci_capitan"] is not None:
            if not _validar_capitan(
                conn,
                id_equipo,
                id_torneo,
                cambios["ci_capitan"],
            ):
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "El capitán debe estar inscrito en este equipo y torneo",
                )

        sets = ", ".join(f"{columna} = %s" for columna in cambios)

        execute(
            conn,
            f"UPDATE equipo SET {sets} WHERE id_equipo = %s",
            (*cambios.values(), id_equipo),
        )

        return _obtener(conn, id_equipo)


@router.delete(
    "/{id_equipo}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def eliminar(id_equipo: IdEquipo, user: AdminUser):
    with get_connection(user.rol) as conn:
        if _obtener(conn, id_equipo) is None:
            raise _no_encontrado()

        execute(
            conn,
            "DELETE FROM equipo WHERE id_equipo = %s",
            (id_equipo,),
        )
