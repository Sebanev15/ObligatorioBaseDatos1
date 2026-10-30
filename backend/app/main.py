import logging

import pymysql
from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse

from .db import fetch_one, get_connection
from .routers import complejos, jugadores, auth

logger = logging.getLogger("torneo")

app = FastAPI(
    title="Torneo Interfacultades de Fútbol 5",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

api = APIRouter(prefix="/api")


@api.get("/health", tags=["sistema"])
def health():
    return {"status": "ok"}


@api.get("/health/db", tags=["sistema"])
def health_db():
    """Comprueba que el backend llega a MySQL con sus credenciales."""
    with get_connection("administrador") as conn:
        fetch_one(conn, "SELECT 1 AS ok")
    return {"status": "ok"}


# --- Routers: uno por entidad -----------------------------------------------------------
api.include_router(jugadores.router)
api.include_router(complejos.router)
api.include_router(auth.router)
app.include_router(api)


# --- Errores de MySQL -> respuestas HTTP claras -----------------------------------------
# El 1644 es el SIGNAL SQLSTATE '45000' de los triggers: el MESSAGE_TEXT del trigger le llega
# tal cual al cliente. El resto son violaciones de constraints (UNIQUE, FK, NOT NULL, CHECK).
_ERRORES = {
    1062: (409, "Ya existe un registro con esos datos."),
    1451: (409, "No se puede eliminar: hay registros que dependen de este."),
    1452: (422, "Referencia inválida: el registro relacionado no existe."),
    1048: (422, "Falta un dato obligatorio."),
    3819: (422, "Los datos no cumplen una restricción de validación."),
    1142: (403, "La base de datos rechazó la operación por falta de permisos."),
    1265: (422, "Valor inválido para un campo con opciones fijas."),
}
_ERRORES_CONEXION = {1045, 2002, 2003, 2006, 2013}


@app.exception_handler(pymysql.MySQLError)
async def mysql_error_handler(request: Request, exc: pymysql.MySQLError):
    codigo = exc.args[0] if exc.args and isinstance(exc.args[0], int) else None
    if codigo == 1644:
        mensaje = exc.args[1] if len(exc.args) > 1 else "Se violó una regla del torneo."
        return JSONResponse(status_code=422, content={"detail": mensaje})
    if codigo in _ERRORES:
        status_http, mensaje = _ERRORES[codigo]
        return JSONResponse(status_code=status_http, content={"detail": mensaje})
    if codigo in _ERRORES_CONEXION:
        logger.error("No se pudo conectar a la base de datos: %s", exc)
        return JSONResponse(status_code=503, content={"detail": "Base de datos no disponible."})
    logger.exception("Error de MySQL no mapeado: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Error interno de base de datos."})