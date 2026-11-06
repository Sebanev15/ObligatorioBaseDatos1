"""Consulta los equipos local y visitante guardados en el partido."""
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from ..db import fetch_all, fetch_one, get_connection
from ..deps import AnyUser
from ..schemas.partido_equipo import PartidoEquipoOut

router = APIRouter(prefix="/partidos/{id_partido}/equipos", tags=["partidos"])
IdPartido = Annotated[int, Path(gt=0)]


@router.get("", response_model=list[PartidoEquipoOut])
def listar(id_partido: IdPartido, user: AnyUser):
    with get_connection(user.rol) as conn:
        if fetch_one(conn, "SELECT 1 FROM partido WHERE id_partido = %s", (id_partido,)) is None:
            raise HTTPException(status_code=404, detail="Partido no encontrado")
        return fetch_all(conn, """SELECT p.id_partido, p.id_equipo_local AS id_equipo, p.id_torneo, e.nombre AS equipo
                                  FROM partido p JOIN equipo e ON e.id_equipo = p.id_equipo_local
                                  WHERE p.id_partido = %s
                                  UNION ALL
                                  SELECT p.id_partido, p.id_equipo_visitante AS id_equipo, p.id_torneo, e.nombre AS equipo
                                  FROM partido p JOIN equipo e ON e.id_equipo = p.id_equipo_visitante
                                  WHERE p.id_partido = %s
                                  ORDER BY equipo""", (id_partido, id_partido))
