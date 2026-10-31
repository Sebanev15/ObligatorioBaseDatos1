"""ABM de sanciones a jugadores.

- Las sanciones por tarjeta roja y por acumulación de 3 amarillas las genera el sistema
  (trigger), no se crean por la API.
- La organización puede aplicar sanciones disciplinarias de varias fechas: eso es lo que crea el POST.
"""
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from ..db import execute, fetch_all, fetch_one, get_connection
from ..deps import AdminUser, AnyUser
from ..schemas.sancion import MotivoSancion, SancionCreate, SancionOut, SancionPatch

router = APIRouter(prefix="/sanciones", tags=["sanciones"])

IdSancion = Annotated[int, Path(gt=0)]

MOTIVO_MANUAL = "disciplinaria"

_SELECT = """
    SELECT s.id_sancion, s.ci_jugador, CONCAT(j.nombre, ' ', j.apellido) AS jugador,
           s.id_torneo, t.nombre AS torneo, s.motivo,
           s.numero_fecha_inicio, s.cantidad_fechas,
           s.numero_fecha_inicio + s.cantidad_fechas - 1 AS numero_fecha_fin
    FROM sancion_jugador s
    JOIN jugador j ON j.ci = s.ci_jugador
    JOIN torneo t  ON t.id_torneo = s.id_torneo
"""


def _obtener(conn, id_sancion: int) -> dict | None:
    return fetch_one(conn, _SELECT + " WHERE s.id_sancion = %s", (id_sancion,))


def _no_encontrada() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "Sanción no encontrada")


@router.get("", response_model=list[SancionOut])
def listar(
    user: AnyUser,
    id_torneo: int | None = None,
    ci_jugador: int | None = None,
    motivo: MotivoSancion | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    # Las condiciones son texto fijo; los valores viajan siempre como parámetros (%s).
    condiciones: list[str] = []
    params: list = []
    if id_torneo is not None:
        condiciones.append("s.id_torneo = %s")
        params.append(id_torneo)
    if ci_jugador is not None:
        condiciones.append("s.ci_jugador = %s")
        params.append(ci_jugador)
    if motivo is not None:
        condiciones.append("s.motivo = %s")
        params.append(motivo)
    where = (" WHERE " + " AND ".join(condiciones)) if condiciones else ""
    sql = _SELECT + where + " ORDER BY s.id_torneo DESC, s.numero_fecha_inicio DESC, s.id_sancion DESC LIMIT %s OFFSET %s"
    with get_connection(user.rol) as conn:
        return fetch_all(conn, sql, (*params, limit, offset))


@router.get("/{id_sancion}", response_model=SancionOut)
def obtener(id_sancion: IdSancion, user: AnyUser):
    with get_connection(user.rol) as conn:
        fila = _obtener(conn, id_sancion)
    if fila is None:
        raise _no_encontrada()
    return fila


@router.post("", response_model=SancionOut, status_code=status.HTTP_201_CREATED)
def crear(data: SancionCreate, user: AdminUser):
    with get_connection(user.rol) as conn:
        if fetch_one(conn, "SELECT 1 AS x FROM jugador WHERE ci = %s", (data.ci_jugador,)) is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"No existe un jugador con CI {data.ci_jugador}")
        if fetch_one(conn, "SELECT 1 AS x FROM torneo WHERE id_torneo = %s", (data.id_torneo,)) is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "El torneo indicado no existe")

        # Solo se puede sancionar a quien integra un plantel en esa edición
        if fetch_one(
            conn,
            "SELECT 1 AS x FROM equipo_jugador_torneo WHERE ci_jugador = %s AND id_torneo = %s",
            (data.ci_jugador, data.id_torneo),
        ) is None:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, "El jugador no integra ningún equipo en este torneo"
            )

        # Evita el doble clic: misma sanción disciplinaria, mismo jugador y misma fecha de inicio
        if fetch_one(
            conn,
            """SELECT id_sancion FROM sancion_jugador
               WHERE ci_jugador = %s AND id_torneo = %s AND motivo = %s AND numero_fecha_inicio = %s""",
            (data.ci_jugador, data.id_torneo, MOTIVO_MANUAL, data.numero_fecha_inicio),
        ) is not None:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"El jugador ya tiene una sanción disciplinaria que empieza en la fecha {data.numero_fecha_inicio}",
            )

        res = execute(
            conn,
            """INSERT INTO sancion_jugador (ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas)
               VALUES (%s, %s, %s, %s, %s)""",
            (data.ci_jugador, data.id_torneo, MOTIVO_MANUAL, data.numero_fecha_inicio, data.cantidad_fechas),
        )
        return _obtener(conn, res.lastrowid)


@router.patch("/{id_sancion}", response_model=SancionOut)
def modificar(id_sancion: IdSancion, data: SancionPatch, user: AdminUser):
    cambios = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    if not cambios:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se envió ningún campo para modificar")

    with get_connection(user.rol) as conn:
        actual = _obtener(conn, id_sancion)
        if actual is None:
            raise _no_encontrada()
        if actual["motivo"] != MOTIVO_MANUAL:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Las sanciones automáticas (roja o acumulación de amarillas) no se modifican. "
                "Si hay un error, eliminala.",
            )
        sets = ", ".join(f"{columna} = %s" for columna in cambios)  # columnas = campos del modelo
        execute(conn, f"UPDATE sancion_jugador SET {sets} WHERE id_sancion = %s", (*cambios.values(), id_sancion))
        return _obtener(conn, id_sancion)


@router.delete("/{id_sancion}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(id_sancion: IdSancion, user: AdminUser):
    # Se puede eliminar cualquier sanción, incluidas las automáticas (por ejemplo, si se anuló una tarjeta).
    with get_connection(user.rol) as conn:
        res = execute(conn, "DELETE FROM sancion_jugador WHERE id_sancion = %s", (id_sancion,))
    if res.rowcount == 0:
        raise _no_encontrada()