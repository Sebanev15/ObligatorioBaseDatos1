from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ColorTarjeta = Literal["amarilla", "roja"]
_CONFIG = ConfigDict(extra="forbid")


class TarjetaCreate(BaseModel):
    model_config = _CONFIG

    ci_jugador: int = Field(ge=1_000_000, le=99_999_999)
    minuto: int = Field(ge=0, le=130)
    color: ColorTarjeta


class TarjetaPatch(BaseModel):
    model_config = _CONFIG

    minuto: int | None = Field(default=None, ge=0, le=130)
    color: ColorTarjeta | None = None


class TarjetaOut(BaseModel):
    id_tarjeta: int
    id_partido: int
    ci_jugador: int
    jugador: str
    id_equipo: int
    equipo: str
    minuto: int
    color: ColorTarjeta
