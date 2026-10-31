from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

EstadoTorneo = Literal["inscripcion", "en curso", "finalizado"]
Semestre = Literal[1, 2]

_CONFIG = ConfigDict(str_strip_whitespace=True, extra="forbid")


class TorneoCreate(BaseModel):
    """El estado no se envía: todo torneo nuevo arranca en 'inscripcion'."""
    model_config = _CONFIG

    nombre: str = Field(min_length=2, max_length=150)
    anio: int = Field(ge=2000, le=2100)
    semestre: Semestre
    fecha_inicio: date
    fecha_fin: date

    @model_validator(mode="after")
    def _fechas_coherentes(self):
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("fecha_fin no puede ser anterior a fecha_inicio")
        return self


class TorneoPatch(BaseModel):
    """Datos generales. El estado se cambia aparte (PATCH /torneos/{id}/estado)."""
    model_config = _CONFIG

    nombre: str | None = Field(default=None, min_length=2, max_length=150)
    anio: int | None = Field(default=None, ge=2000, le=2100)
    semestre: Semestre | None = None
    fecha_inicio: date | None = None
    fecha_fin: date | None = None


class TorneoEstadoPatch(BaseModel):
    model_config = _CONFIG

    estado: EstadoTorneo


class TorneoOut(BaseModel):
    id_torneo: int
    nombre: str
    anio: int
    semestre: int
    fecha_inicio: date
    fecha_fin: date
    estado: EstadoTorneo