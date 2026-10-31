
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, status

from ..db import execute, fetch_all, fetch_one, get_connection
from ..deps import AdminUser, AnyUser
from ..schemas.equipo_jugador_torneo import (
    InscripcionCreate,
    InscripcionOut,
    InscripcionPatch,
)

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
        equipo = _equipo(conn, id_equipo)
        if equipo is None:
            raise _no_encontrado()

        jugador = fetch_one(
            conn,
            "SELECT ci FROM jugador WHERE ci = %s",
            (data.ci_jugador,),
        )
        if jugador is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "Jugador no encontrado",
            )

        existente = fetch_one(
            conn,
            """
                SELECT id_equipo
                FROM equipo_jugador_torneo
                WHERE ci_jugador = %s
                  AND id_torneo = %s
            """,
            (data.ci_jugador, equipo["id_torneo"]),
        )
        if existente is not None:
            raise _conflicto(
                "El jugador ya está inscrito en un equipo de este torneo"
            )

        camiseta = fetch_one(
            conn,
            """
                SELECT ci_jugador
                FROM equipo_jugador_torneo
                WHERE id_equipo = %s
                  AND numero_camiseta = %s
            """,
            (id_equipo, data.numero_camiseta),
        )
        if camiseta is not None:
            raise _conflicto(
                "Ese número de camiseta ya está ocupado en el equipo"
            )

        execute(
            conn,
            """
                INSERT INTO equipo_jugador_torneo
                    (id_equipo, ci_jugador, id_torneo, numero_camiseta)
                VALUES (%s, %s, %s, %s)
            """,
            (
                id_equipo,
                data.ci_jugador,
                equipo["id_torneo"],
                data.numero_camiseta,
            ),
        )

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
        if _equipo(conn, id_equipo) is None:
            raise _no_encontrado()

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
        equipo = _equipo(conn, id_equipo)
        if equipo is None:
            raise _no_encontrado()

        fila = _inscripcion(conn, id_equipo, ci)
        if fila is None:
            raise _inscripcion_no_encontrada()

        capitan = fetch_one(
            conn,
            """
                SELECT id_equipo
                FROM equipo
                WHERE id_equipo = %s AND ci_capitan = %s
            """,
            (id_equipo, ci),
        )
        if capitan is not None:
            raise _conflicto(
                "Debes asignar otro capitán o quitar el capitán "
                "antes de desinscribir a este jugador"
            )

        execute(
            conn,
            """
                DELETE FROM equipo_jugador_torneo
                WHERE id_equipo = %s AND ci_jugador = %s
            """,
            (id_equipo, ci),
        )
