"""ABM de equipos y de sus planteles (tabla equipo_jugador_torneo)."""
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from ..db import execute, fetch_all, fetch_one, get_connection
from ..deps import AdminUser, AnyUser
from ..schemas.equipo import (
    CamisetaPatch, EquipoCreate, EquipoOut, EquipoPatch, JugadorCandidatoOut,
    JugadorPlantelOut, JugadorPlantelIn,
)
from ._deletion import eliminar_equipo, eliminar_participacion

router = APIRouter(prefix="/equipos", tags=["equipos"])

IdEquipo = Annotated[int, Path(gt=0)]
CIPath = Annotated[int, Path(ge=1_000_000, le=99_999_999, description="Cédula sin puntos ni guion")]

MAX_PLANTEL = 10
MAX_DOCENTES_FUNCIONARIOS = 2

_SELECT = """
    SELECT e.id_equipo, e.nombre, e.id_torneo, t.nombre AS torneo,
           e.id_facultad, f.nombre AS facultad, e.ci_capitan,
           CONCAT(c.nombre, ' ', c.apellido) AS capitan,
           (SELECT COUNT(*) FROM equipo_jugador_torneo ejt
             WHERE ejt.id_equipo = e.id_equipo) AS cantidad_jugadores
    FROM equipo e
    JOIN torneo t   ON t.id_torneo = e.id_torneo
    JOIN facultad f ON f.id_facultad = e.id_facultad
    LEFT JOIN jugador c ON c.ci = e.ci_capitan
"""

_SELECT_PLANTEL = """
    SELECT j.ci, j.nombre, j.apellido, j.tipo, ejt.numero_camiseta,
           COALESCE(e.ci_capitan = j.ci, 0) AS es_capitan
    FROM equipo_jugador_torneo ejt
    JOIN jugador j ON j.ci = ejt.ci_jugador
    JOIN equipo e  ON e.id_equipo = ejt.id_equipo
"""


# ------------------------------------------------------------------ helpers de lectura
def _obtener(conn, id_equipo: int) -> dict | None:
    return fetch_one(conn, _SELECT + " WHERE e.id_equipo = %s", (id_equipo,))


def _plantel_de(conn, id_equipo: int, ci: int) -> dict | None:
    return fetch_one(conn, _SELECT_PLANTEL + " WHERE ejt.id_equipo = %s AND ejt.ci_jugador = %s", (id_equipo, ci))


def _equipo_no_encontrado() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "Equipo no encontrado")


def _equipo_bloqueado(conn, id_equipo: int) -> dict:
    """Lee el equipo con FOR UPDATE: dos cambios de plantel del mismo equipo no se pisan entre sí,
    así el conteo de jugadores (máx. 10, máx. 2 docentes/funcionarios) no se puede burlar con
    dos pedidos simultáneos."""
    fila = fetch_one(
        conn,
        "SELECT id_equipo, nombre, id_torneo, id_facultad, ci_capitan FROM equipo WHERE id_equipo = %s FOR UPDATE",
        (id_equipo,),
    )
    if fila is None:
        raise _equipo_no_encontrado()
    return fila


def _exigir_inscripcion(conn, id_torneo: int) -> None:
    """Los equipos y planteles solo se modifican mientras el torneo está en inscripción."""
    # FOR SHARE: mientras esta operacion no termine, nadie puede cambiar el estado del torneo
    # (el UPDATE de PATCH /torneos/{id}/estado espera), asi no se inscribe a nadie "a ultimo momento".
    torneo = fetch_one(conn, "SELECT estado FROM torneo WHERE id_torneo = %s FOR SHARE", (id_torneo,))
    if torneo is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "El torneo indicado no existe")
    if torneo["estado"] != "inscripcion":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "El torneo no está en etapa de inscripción: los equipos y planteles ya no se pueden modificar",
        )


def _camiseta_ocupada(conn, id_equipo: int, camiseta: int) -> int | None:
    fila = fetch_one(
        conn,
        "SELECT ci_jugador FROM equipo_jugador_torneo WHERE id_equipo = %s AND numero_camiseta = %s",
        (id_equipo, camiseta),
    )
    return fila["ci_jugador"] if fila else None


# ------------------------------------------------------- reglas del plantel (una sola vez)
def _agregar_jugador(conn, equipo: dict, ci: int, camiseta: int) -> None:
    """Valida las reglas del enunciado e inscribe al jugador. La usan 'crear equipo' y
    'agregar jugador', así las reglas viven en un solo lugar."""
    jugador = fetch_one(conn, "SELECT ci, nombre, apellido, id_facultad, tipo FROM jugador WHERE ci = %s", (ci,))
    if jugador is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No existe un jugador con CI {ci}")

    # Todos los jugadores deben pertenecer a la facultad del equipo
    if jugador["id_facultad"] != equipo["id_facultad"]:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "El jugador no pertenece a la facultad del equipo")

    # Un jugador no puede integrar más de un equipo en la misma edición
    otro = fetch_one(
        conn,
        """SELECT e.nombre FROM equipo_jugador_torneo ejt
           JOIN equipo e ON e.id_equipo = ejt.id_equipo
           WHERE ejt.ci_jugador = %s AND ejt.id_torneo = %s""",
        (ci, equipo["id_torneo"]),
    )
    if otro is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"El jugador ya integra el equipo {otro['nombre']} en este torneo")

    # Plantel de 5 a 10 (el máximo se controla acá; el mínimo al programar partidos)
    cuenta = fetch_one(
        conn,
        """SELECT COUNT(*) AS total,
                  COALESCE(SUM(j.tipo IN ('docente', 'funcionario')), 0) AS no_estudiantes
           FROM equipo_jugador_torneo ejt
           JOIN jugador j ON j.ci = ejt.ci_jugador
           WHERE ejt.id_equipo = %s""",
        (equipo["id_equipo"],),
    )
    if cuenta["total"] >= MAX_PLANTEL:
        raise HTTPException(status.HTTP_409_CONFLICT, f"El plantel ya tiene {MAX_PLANTEL} jugadores")

    # Como máximo 2 docentes o funcionarios por plantel
    if jugador["tipo"] in ("docente", "funcionario") and int(cuenta["no_estudiantes"]) >= MAX_DOCENTES_FUNCIONARIOS:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Cada plantel admite como máximo {MAX_DOCENTES_FUNCIONARIOS} docentes o funcionarios",
        )

    if _camiseta_ocupada(conn, equipo["id_equipo"], camiseta) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"La camiseta {camiseta} ya está asignada en este equipo")

    execute(
        conn,
        """INSERT INTO equipo_jugador_torneo (id_equipo, ci_jugador, id_torneo, numero_camiseta)
           VALUES (%s, %s, %s, %s)""",
        (equipo["id_equipo"], ci, equipo["id_torneo"], camiseta),
    )


# ================================================================================ EQUIPOS
@router.get("", response_model=list[EquipoOut])
def listar(
    user: AnyUser,
    id_torneo: int | None = None,
    id_facultad: int | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    condiciones: list[str] = []
    params: list = []
    if id_torneo is not None:
        condiciones.append("e.id_torneo = %s")
        params.append(id_torneo)
    if id_facultad is not None:
        condiciones.append("e.id_facultad = %s")
        params.append(id_facultad)
    where = (" WHERE " + " AND ".join(condiciones)) if condiciones else ""
    sql = _SELECT + where + " ORDER BY t.anio DESC, t.semestre DESC, e.nombre LIMIT %s OFFSET %s"
    with get_connection(user.rol) as conn:
        return fetch_all(conn, sql, (*params, limit, offset))


@router.get("/{id_equipo}", response_model=EquipoOut)
def obtener(id_equipo: IdEquipo, user: AnyUser):
    with get_connection(user.rol) as conn:
        fila = _obtener(conn, id_equipo)
    if fila is None:
        raise _equipo_no_encontrado()
    return fila


@router.post("", response_model=EquipoOut, status_code=status.HTTP_201_CREATED)
def crear(data: EquipoCreate, user: AdminUser):
    with get_connection(user.rol) as conn:
        _exigir_inscripcion(conn, data.id_torneo)

        if fetch_one(conn, "SELECT 1 AS x FROM facultad WHERE id_facultad = %s", (data.id_facultad,)) is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "La facultad indicada no existe")
        if fetch_one(
            conn, "SELECT id_equipo FROM equipo WHERE nombre = %s AND id_torneo = %s", (data.nombre, data.id_torneo)
        ) is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, f"Ya existe un equipo llamado {data.nombre} en este torneo")

        res = execute(
            conn,
            "INSERT INTO equipo (nombre, id_torneo, id_facultad) VALUES (%s, %s, %s)",
            (data.nombre, data.id_torneo, data.id_facultad),
        )
        id_equipo = res.lastrowid
        equipo = {"id_equipo": id_equipo, "id_torneo": data.id_torneo, "id_facultad": data.id_facultad}

        for j in data.jugadores:
            _agregar_jugador(conn, equipo, j.ci_jugador, j.numero_camiseta)

        if data.ci_capitan is not None:
            execute(conn, "UPDATE equipo SET ci_capitan = %s WHERE id_equipo = %s", (data.ci_capitan, id_equipo))

        return _obtener(conn, id_equipo)


@router.patch("/{id_equipo}", response_model=EquipoOut)
def modificar(id_equipo: IdEquipo, data: EquipoPatch, user: AdminUser):
    cambios = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    if not cambios:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se envió ningún campo para modificar")

    with get_connection(user.rol) as conn:
        equipo = _equipo_bloqueado(conn, id_equipo)
        id_torneo_nuevo = cambios.get("id_torneo", equipo["id_torneo"])
        id_facultad_nueva = cambios.get("id_facultad", equipo["id_facultad"])
        cambia_torneo = id_torneo_nuevo != equipo["id_torneo"]

        if "id_torneo" in cambios or "id_facultad" in cambios:
            _exigir_inscripcion(conn, equipo["id_torneo"])
            _exigir_inscripcion(conn, id_torneo_nuevo)

        if "id_facultad" in cambios and fetch_one(
            conn,
            "SELECT id_facultad FROM facultad WHERE id_facultad = %s",
            (id_facultad_nueva,),
        ) is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "La facultad indicada no existe")

        plantel = fetch_all(
            conn,
            """SELECT ejt.ci_jugador, ejt.numero_camiseta, j.id_facultad
               FROM equipo_jugador_torneo ejt
               JOIN jugador j ON j.ci = ejt.ci_jugador
               WHERE ejt.id_equipo = %s""",
            (id_equipo,),
        )
        if any(jugador["id_facultad"] != id_facultad_nueva for jugador in plantel):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "No se puede cambiar la facultad: todos los jugadores del plantel deben pertenecer a ella",
            )

        if cambia_torneo:
            partido = fetch_one(
                conn,
                """SELECT id_partido FROM partido
                   WHERE id_equipo_local = %s OR id_equipo_visitante = %s
                   LIMIT 1""",
                (id_equipo, id_equipo),
            )
            if partido is not None:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    "No se puede cambiar el torneo de un equipo que ya tiene partidos asignados",
                )

            for jugador in plantel:
                ya_inscrito = fetch_one(
                    conn,
                    """SELECT id_equipo FROM equipo_jugador_torneo
                       WHERE ci_jugador = %s AND id_torneo = %s""",
                    (jugador["ci_jugador"], id_torneo_nuevo),
                )
                if ya_inscrito is not None:
                    raise HTTPException(
                        status.HTTP_409_CONFLICT,
                        "No se puede cambiar el torneo: un jugador del plantel ya integra otro equipo en el torneo seleccionado",
                    )

        if "nombre" in cambios or cambia_torneo:
            nombre_nuevo = cambios.get("nombre", equipo["nombre"])
            repetido = fetch_one(
                conn,
                "SELECT id_equipo FROM equipo WHERE nombre = %s AND id_torneo = %s",
                (nombre_nuevo, id_torneo_nuevo),
            )
            if repetido is not None and repetido["id_equipo"] != id_equipo:
                raise HTTPException(status.HTTP_409_CONFLICT, f"Ya existe un equipo llamado {nombre_nuevo} en este torneo")

        if "ci_capitan" in cambios and _plantel_de(conn, id_equipo, cambios["ci_capitan"]) is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "El capitán debe ser un jugador del plantel del equipo")

        if cambia_torneo:
            execute(conn, "UPDATE equipo SET ci_capitan = NULL WHERE id_equipo = %s", (id_equipo,))
            execute(conn, "DELETE FROM equipo_jugador_torneo WHERE id_equipo = %s", (id_equipo,))

        cambios_equipo = {key: value for key, value in cambios.items() if not (cambia_torneo and key == "ci_capitan")}
        if cambios_equipo:
            sets = ", ".join(f"{columna} = %s" for columna in cambios_equipo)
            execute(conn, f"UPDATE equipo SET {sets} WHERE id_equipo = %s", (*cambios_equipo.values(), id_equipo))

        if cambia_torneo:
            for jugador in plantel:
                execute(
                    conn,
                    """INSERT INTO equipo_jugador_torneo
                       (id_equipo, ci_jugador, id_torneo, numero_camiseta)
                       VALUES (%s, %s, %s, %s)""",
                    (id_equipo, jugador["ci_jugador"], id_torneo_nuevo, jugador["numero_camiseta"]),
                )
            ci_capitan_nuevo = cambios.get("ci_capitan", equipo["ci_capitan"])
            if ci_capitan_nuevo is not None:
                execute(
                    conn,
                    "UPDATE equipo SET ci_capitan = %s WHERE id_equipo = %s",
                    (ci_capitan_nuevo, id_equipo),
                )

        return _obtener(conn, id_equipo)


@router.delete("/{id_equipo}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(id_equipo: IdEquipo, user: AdminUser):
    with get_connection(user.rol) as conn:
        _equipo_bloqueado(conn, id_equipo)
        eliminar_equipo(conn, id_equipo)


# ================================================================================ PLANTEL
@router.get("/{id_equipo}/jugadores", response_model=list[JugadorPlantelOut], tags=["plantel"])
def listar_plantel(id_equipo: IdEquipo, user: AnyUser):
    with get_connection(user.rol) as conn:
        if _obtener(conn, id_equipo) is None:
            raise _equipo_no_encontrado()
        return fetch_all(
            conn, _SELECT_PLANTEL + " WHERE ejt.id_equipo = %s ORDER BY ejt.numero_camiseta", (id_equipo,)
        )


@router.get(
    "/{id_equipo}/jugadores/candidatos",
    response_model=list[JugadorCandidatoOut],
    tags=["plantel"],
)
def listar_candidatos_plantel(id_equipo: IdEquipo, user: AdminUser):
    with get_connection(user.rol) as conn:
        equipo = fetch_one(
            conn,
            """
                SELECT e.id_torneo, e.id_facultad, t.estado,
                       (SELECT COUNT(*) FROM equipo_jugador_torneo ejt
                        WHERE ejt.id_equipo = e.id_equipo) AS cantidad_jugadores,
                       (SELECT COUNT(*)
                        FROM equipo_jugador_torneo ejt
                        JOIN jugador inscrito ON inscrito.ci = ejt.ci_jugador
                        WHERE ejt.id_equipo = e.id_equipo
                          AND inscrito.tipo IN ('docente', 'funcionario')) AS cantidad_docentes_funcionarios
                FROM equipo e
                JOIN torneo t ON t.id_torneo = e.id_torneo
                WHERE e.id_equipo = %s
            """,
            (id_equipo,),
        )
        if equipo is None:
            raise _equipo_no_encontrado()

        candidatos = fetch_all(
            conn,
            """
                SELECT j.ci, j.nombre, j.apellido, j.tipo,
                       CASE
                           WHEN %s <> 'inscripcion' THEN 0
                           WHEN j.id_facultad <> %s THEN 0
                           WHEN EXISTS (
                               SELECT 1 FROM equipo_jugador_torneo inscr
                               WHERE inscr.ci_jugador = j.ci AND inscr.id_torneo = %s
                           ) THEN 0
                           WHEN %s >= %s THEN 0
                           WHEN j.tipo IN ('docente', 'funcionario') AND %s >= %s THEN 0
                           ELSE 1
                       END AS puede_agregar,
                       CASE
                           WHEN %s <> 'inscripcion' THEN 'El torneo no está en etapa de inscripción'
                           WHEN j.id_facultad <> %s THEN 'No pertenece a la facultad del equipo'
                           WHEN EXISTS (
                               SELECT 1 FROM equipo_jugador_torneo inscr
                               WHERE inscr.ci_jugador = j.ci AND inscr.id_torneo = %s
                           ) THEN 'Ya integra un equipo de este torneo'
                           WHEN %s >= %s THEN 'El plantel ya alcanzó el máximo de 10 jugadores'
                           WHEN j.tipo IN ('docente', 'funcionario') AND %s >= %s
                               THEN 'El plantel ya alcanzó el máximo de 2 docentes o funcionarios'
                           ELSE NULL
                       END AS motivo
                FROM jugador j
                ORDER BY j.apellido, j.nombre, j.ci
            """,
            (
                equipo["estado"], equipo["id_facultad"], equipo["id_torneo"],
                equipo["cantidad_jugadores"], MAX_PLANTEL,
                equipo["cantidad_docentes_funcionarios"], MAX_DOCENTES_FUNCIONARIOS,
                equipo["estado"], equipo["id_facultad"], equipo["id_torneo"],
                equipo["cantidad_jugadores"], MAX_PLANTEL,
                equipo["cantidad_docentes_funcionarios"], MAX_DOCENTES_FUNCIONARIOS,
            ),
        )
        return candidatos


@router.post("/{id_equipo}/jugadores", response_model=JugadorPlantelOut,
             status_code=status.HTTP_201_CREATED, tags=["plantel"])
def agregar_jugador(id_equipo: IdEquipo, data: JugadorPlantelIn, user: AdminUser):
    with get_connection(user.rol) as conn:
        equipo = _equipo_bloqueado(conn, id_equipo)
        _exigir_inscripcion(conn, equipo["id_torneo"])
        _agregar_jugador(conn, equipo, data.ci_jugador, data.numero_camiseta)
        return _plantel_de(conn, id_equipo, data.ci_jugador)


@router.patch("/{id_equipo}/jugadores/{ci}", response_model=JugadorPlantelOut, tags=["plantel"])
def cambiar_camiseta(id_equipo: IdEquipo, ci: CIPath, data: CamisetaPatch, user: AdminUser):
    with get_connection(user.rol) as conn:
        equipo = _equipo_bloqueado(conn, id_equipo)
        _exigir_inscripcion(conn, equipo["id_torneo"])
        if _plantel_de(conn, id_equipo, ci) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El jugador no integra este equipo")
        ocupada_por = _camiseta_ocupada(conn, id_equipo, data.numero_camiseta)
        if ocupada_por is not None and ocupada_por != ci:
            raise HTTPException(status.HTTP_409_CONFLICT, f"La camiseta {data.numero_camiseta} ya está asignada en este equipo")
        execute(
            conn,
            "UPDATE equipo_jugador_torneo SET numero_camiseta = %s WHERE id_equipo = %s AND ci_jugador = %s",
            (data.numero_camiseta, id_equipo, ci),
        )
        return _plantel_de(conn, id_equipo, ci)


@router.delete("/{id_equipo}/jugadores/{ci}", status_code=status.HTTP_204_NO_CONTENT, tags=["plantel"])
def quitar_jugador(id_equipo: IdEquipo, ci: CIPath, user: AdminUser):
    with get_connection(user.rol) as conn:
        equipo = _equipo_bloqueado(conn, id_equipo)
        _exigir_inscripcion(conn, equipo["id_torneo"])
        if _plantel_de(conn, id_equipo, ci) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El jugador no integra este equipo")

        eliminar_participacion(conn, id_equipo, ci)
        execute(
            conn,
            "UPDATE equipo SET ci_capitan = NULL WHERE id_equipo = %s AND ci_capitan = %s",
            (id_equipo, ci),
        )
        res = execute(conn, "DELETE FROM equipo_jugador_torneo WHERE id_equipo = %s AND ci_jugador = %s", (id_equipo, ci))
        if res.rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "El jugador no integra este equipo")