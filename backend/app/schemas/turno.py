from datetime import time

from pydantic import BaseModel, ConfigDict, model_validator

_CONFIG = ConfigDict(extra="forbid")


class TurnoCreate(BaseModel):
    model_config = _CONFIG

    hora_inicio: time
    hora_fin: time

    @model_validator(mode="after")
    def validar_horas(self):
        if self.hora_fin <= self.hora_inicio:
            raise ValueError("hora_fin debe ser posterior a hora_inicio")
        return self


class TurnoPatch(BaseModel):
    model_config = _CONFIG

    hora_inicio: time | None = None
    hora_fin: time | None = None


class TurnoOut(BaseModel):
    id_turno: int
    hora_inicio: time
    hora_fin: time
