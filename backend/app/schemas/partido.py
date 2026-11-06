from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

EstadoPartido = Literal["programado", "jugado", "postergado", "cancelado"]

_CONFIG = ConfigDict(extra="forbid", str_strip_whitespace=True)


class PartidoCreate(BaseModel):
    model_config = _CONFIG

    id_torneo: int = Field(gt=0)
    numero_fecha: int = Field(gt=0)
    id_equipo_local: int = Field(gt=0)
    id_equipo_visitante: int = Field(gt=0)
    dia: date
    id_turno: int = Field(gt=0)
    nombre_cancha: str = Field(min_length=1, max_length=100)
    id_complejo: int = Field(gt=0)


class PartidoPatch(BaseModel):
    """La edición no cambia: para mover un partido se modifican sus datos de agenda."""
    model_config = _CONFIG

    numero_fecha: int | None = Field(default=None, gt=0)
    id_equipo_local: int | None = Field(default=None, gt=0)
    id_equipo_visitante: int | None = Field(default=None, gt=0)
    dia: date | None = None
    id_turno: int | None = Field(default=None, gt=0)
    nombre_cancha: str | None = Field(default=None, min_length=1, max_length=100)
    id_complejo: int | None = Field(default=None, gt=0)
    estado: EstadoPartido | None = None


class PartidoOut(BaseModel):
    id_partido: int
    id_torneo: int
    torneo: str
    numero_fecha: int
    id_equipo_local: int
    equipo_local: str
    id_equipo_visitante: int
    equipo_visitante: str
    dia: date
    id_turno: int
    hora_inicio: str
    hora_fin: str
    nombre_cancha: str
    id_complejo: int
    complejo: str
    estado: EstadoPartido
    goles_local: int
    goles_visitante: int
