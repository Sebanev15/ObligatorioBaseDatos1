"""ABM de torneos (una edición por semestre) y sus cambios de estado."""
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from ..db import execute, fetch_all, fetch_one, get_connection
from ..deps import AdminUser, AnyUser
from ..schemas.torneo import (
    EstadoTorneo, TorneoCreate, TorneoEstadoPatch, TorneoOut, TorneoPatch,
)

router = APIRouter(prefix="/torneos", tags=["torneos"])

IdTorneo = Annotated[int, Path(gt=0)]

_SELECT = "SELECT id_torneo, nombre, anio, semestre, fecha_inicio, fecha_fin, estado FROM torneo"

# El torneo solo avanza de a un paso, en este orden.
_ORDEN_ESTADOS = ["inscripcion", "en curso", "finalizado"]


def _obtener(conn, id_torneo: int) -> dict | None:
    return fetch_one(conn, _SELECT + " WHERE id_torneo = %s", (id_torneo,))


def _no_encontrado() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "Torneo no encontrado")


def _exigir_edicion_libre(conn, anio: int, semestre: int, id_torneo: int | None = None) -> None:
    """Una edición por semestre: no puede haber dos torneos con el mismo año y semestre."""
    otro = fetch_one(conn, "SELECT id_torneo FROM torneo WHERE anio = %s AND semestre = %s", (anio, semestre))
    if otro is not None and otro["id_torneo"] != id_torneo:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Ya existe un torneo para el año {anio}, semestre {semestre}")


@router.get("", response_model=list[TorneoOut])
def listar(
        user: AnyUser,
        estado: EstadoTorneo | None = None,
        anio: int | None = None,
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
):
    condiciones: list[str] = []
    params: list = []
    if estado is not None:
        condiciones.append("estado = %s")
        params.append(estado)
    if anio is not None:
        condiciones.append("anio = %s")
        params.append(anio)
    where = (" WHERE " + " AND ".join(condiciones)) if condiciones else ""
    sql = _SELECT + where + " ORDER BY anio DESC, semestre DESC LIMIT %s OFFSET %s"
    with get_connection(user.rol) as conn:
        return fetch_all(conn, sql, (*params, limit, offset))


@router.get("/{id_torneo}", response_model=TorneoOut)
def obtener(id_torneo: IdTorneo, user: AnyUser):
    with get_connection(user.rol) as conn:
        fila = _obtener(conn, id_torneo)
    if fila is None:
        raise _no_encontrado()
    return fila


@router.post("", response_model=TorneoOut, status_code=status.HTTP_201_CREATED)
def crear(data: TorneoCreate, user: AdminUser):
    with get_connection(user.rol) as conn:
        _exigir_edicion_libre(conn, data.anio, data.semestre)
        res = execute(
            conn,
            """INSERT INTO torneo (nombre, anio, semestre, fecha_inicio, fecha_fin)
               VALUES (%s, %s, %s, %s, %s)""",   # el estado toma el DEFAULT 'inscripcion'
            (data.nombre, data.anio, data.semestre, data.fecha_inicio, data.fecha_fin),
        )
        return _obtener(conn, res.lastrowid)


@router.patch("/{id_torneo}", response_model=TorneoOut)
def modificar(id_torneo: IdTorneo, data: TorneoPatch, user: AdminUser):
    cambios = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    if not cambios:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se envió ningún campo para modificar")

    with get_connection(user.rol) as conn:
        actual = _obtener(conn, id_torneo)
        if actual is None:
            raise _no_encontrado()

        # Las reglas se validan sobre el resultado final (lo que ya había + lo que cambia),
        # porque el cliente puede mandar solo una de las dos fechas.
        nuevo = {**actual, **cambios}
        if nuevo["fecha_fin"] < nuevo["fecha_inicio"]:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "fecha_fin no puede ser anterior a fecha_inicio")
        if "anio" in cambios or "semestre" in cambios:
            _exigir_edicion_libre(conn, nuevo["anio"], nuevo["semestre"], id_torneo)

        sets = ", ".join(f"{columna} = %s" for columna in cambios)  # columnas = campos del modelo
        execute(conn, f"UPDATE torneo SET {sets} WHERE id_torneo = %s", (*cambios.values(), id_torneo))
        return _obtener(conn, id_torneo)


@router.patch("/{id_torneo}/estado", response_model=TorneoOut)
def cambiar_estado(id_torneo: IdTorneo, data: TorneoEstadoPatch, user: AdminUser):
    """inscripcion -> en curso -> finalizado. No se puede saltear ni volver atrás."""
    with get_connection(user.rol) as conn:
        actual = _obtener(conn, id_torneo)
        if actual is None:
            raise _no_encontrado()
        if _ORDEN_ESTADOS.index(data.estado) != _ORDEN_ESTADOS.index(actual["estado"]) + 1:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"No se puede pasar de '{actual['estado']}' a '{data.estado}'. "
                "El orden es: inscripcion → en curso → finalizado",
            )
        execute(conn, "UPDATE torneo SET estado = %s WHERE id_torneo = %s", (data.estado, id_torneo))
        return _obtener(conn, id_torneo)


@router.delete("/{id_torneo}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(id_torneo: IdTorneo, user: AdminUser):
    # Si tiene equipos, partidos o sanciones, MySQL rechaza el DELETE (error 1451) y main.py responde 409.
    with get_connection(user.rol) as conn:
        res = execute(conn, "DELETE FROM torneo WHERE id_torneo = %s", (id_torneo,))
    if res.rowcount == 0:
        raise _no_encontrado()