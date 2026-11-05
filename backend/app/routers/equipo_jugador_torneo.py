
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, status

from ..db import execute, fetch_all, fetch_one, get_connection
from ..deps import AdminUser, AnyUser
from ..schemas.equipo_jugador_torneo import (
    InscripcionCreate,
    InscripcionOut,
    InscripcionPatch,
)
from ._deletion import eliminar_participacion
from .equipos import _agregar_jugador, _equipo_bloqueado, _exigir_inscripcion

router = APIRouter(
    prefix="/equipos/{id_equipo}/jugadores",
    tags=["inscripciones"],
)

IdEquipo = Annotated[int, Path(gt=0)]
CI = Annotated[
    int,
    Path(ge=1_000_000, le=99_999_999),
]

_SELECT = """
    SELECT ejt.id_equipo, ejt.ci_jugador, ejt.id_torneo,
           ejt.numero_camiseta, j.nombre, j.apellido
    FROM equipo_jugador_torneo ejt
    JOIN jugador j ON j.ci = ejt.ci_jugador
"""


def _equipo(conn, id_equipo: int) -> dict | None:
    return fetch_one(
        conn,
        """
            SELECT id_equipo, id_torneo
            FROM equipo
            WHERE id_equipo = %s
        """,
        (id_equipo,),
    )


def _inscripcion(
    conn,
    id_equipo: int,
    ci: int,
) -> dict | None:
    return fetch_one(
        conn,
        _SELECT + """
            WHERE ejt.id_equipo = %s
              AND ejt.ci_jugador = %s
        """,
        (id_equipo, ci),
    )


def _no_encontrado() -> HTTPException:
    return HTTPException(
        status.HTTP_404_NOT_FOUND,
        "Equipo no encontrado",
    )


def _inscripcion_no_encontrada() -> HTTPException:
    return HTTPException(
        status.HTTP_404_NOT_FOUND,
        "El jugador no está inscrito en este equipo",
    )


def _conflicto(mensaje: str) -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, mensaje)


@router.get("", response_model=list[InscripcionOut])
def listar(id_equipo: IdEquipo, user: AnyUser):
    with get_connection(user.rol) as conn:
        if _equipo(conn, id_equipo) is None:
            raise _no_encontrado()

        return fetch_all(
            conn,
            _SELECT + """
                WHERE ejt.id_equipo = %s
                ORDER BY j.apellido, j.nombre
            """,
            (id_equipo,),
        )


@router.post(
    "",
    response_model=InscripcionOut,
    status_code=status.HTTP_201_CREATED,
)
def inscribir(
    id_equipo: IdEquipo,
    data: InscripcionCreate,
    user: AdminUser,
):
    with get_connection(user.rol) as conn:
        equipo = _equipo_bloqueado(conn, id_equipo)
        _exigir_inscripcion(conn, equipo["id_torneo"])
        _agregar_jugador(conn, equipo, data.ci_jugador, data.numero_camiseta)

        return _inscripcion(conn, id_equipo, data.ci_jugador)


@router.patch("/{ci}", response_model=InscripcionOut)
def modificar(
    id_equipo: IdEquipo,
    ci: CI,
    data: InscripcionPatch,
    user: AdminUser,
):
    cambios = data.model_dump(exclude_unset=True)

    if not cambios or cambios["numero_camiseta"] is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Debes enviar un número de camiseta válido",
        )

    with get_connection(user.rol) as conn:
        equipo = _equipo_bloqueado(conn, id_equipo)
        _exigir_inscripcion(conn, equipo["id_torneo"])

        fila = _inscripcion(conn, id_equipo, ci)
        if fila is None:
            raise _inscripcion_no_encontrada()

        otra = fetch_one(
            conn,
            """
                SELECT ci_jugador
                FROM equipo_jugador_torneo
                WHERE id_equipo = %s
                  AND numero_camiseta = %s
                  AND ci_jugador <> %s
            """,
            (id_equipo, cambios["numero_camiseta"], ci),
        )
        if otra is not None:
            raise _conflicto(
                "Ese número de camiseta ya está ocupado en el equipo"
            )

        execute(
            conn,
            """
                UPDATE equipo_jugador_torneo
                SET numero_camiseta = %s
                WHERE id_equipo = %s AND ci_jugador = %s
            """,
            (cambios["numero_camiseta"], id_equipo, ci),
        )

        return _inscripcion(conn, id_equipo, ci)


@router.delete(
    "/{ci}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def desinscribir(
    id_equipo: IdEquipo,
    ci: CI,
    user: AdminUser,
):
    with get_connection(user.rol) as conn:
        equipo = _equipo_bloqueado(conn, id_equipo)
        _exigir_inscripcion(conn, equipo["id_torneo"])

        fila = _inscripcion(conn, id_equipo, ci)
        if fila is None:
            raise _inscripcion_no_encontrada()

        eliminar_participacion(conn, id_equipo, ci)
        execute(
            conn,
            "UPDATE equipo SET ci_capitan = NULL WHERE id_equipo = %s AND ci_capitan = %s",
            (id_equipo, ci),
        )

        execute(
            conn,
            """
                DELETE FROM equipo_jugador_torneo
                WHERE id_equipo = %s AND ci_jugador = %s
            """,
            (id_equipo, ci),
        )
