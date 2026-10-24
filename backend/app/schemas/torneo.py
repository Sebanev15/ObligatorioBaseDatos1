
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


EstadoTorneo = Literal["inscripcion", "en curso", "finalizado"]


class TorneoCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    nombre: str = Field(min_length=2, max_length=150)
    anio: int = Field(ge=1, le=9999)
    semestre: int = Field(ge=1, le=2)
    fecha_inicio: date
    fecha_fin: date
    estado: EstadoTorneo = "inscripcion"

    @model_validator(mode="after")
    def validar_fechas(self):
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError(
                "La fecha de fin debe ser posterior o igual a la fecha de inicio"
            )
        return self


class TorneoPatch(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    nombre: str | None = Field(default=None, min_length=2, max_length=150)
    anio: int | None = Field(default=None, ge=1, le=9999)
    semestre: int | None = Field(default=None, ge=1, le=2)
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    estado: EstadoTorneo | None = None


class TorneoOut(BaseModel):
    id_torneo: int
    nombre: str
    anio: int
    semestre: int
    fecha_inicio: date
    fecha_fin: date
    estado: EstadoTorneo
