from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .jugador import TipoJugador

_CONFIG = ConfigDict(str_strip_whitespace=True, extra="forbid")

CI = Annotated[int, Field(ge=1_000_000, le=99_999_999)]
Camiseta = Annotated[int, Field(ge=1, le=99)]


# ---- Plantel --------------------------------------------------------------------------
class JugadorPlantelIn(BaseModel):
    model_config = _CONFIG

    ci_jugador: CI
    numero_camiseta: Camiseta


class CamisetaPatch(BaseModel):
    model_config = _CONFIG

    numero_camiseta: Camiseta


class JugadorPlantelOut(BaseModel):
    ci: int
    nombre: str
    apellido: str
    tipo: TipoJugador
    numero_camiseta: int
    es_capitan: bool


# ---- Equipo ---------------------------------------------------------------------------
class EquipoCreate(BaseModel):
    """Se puede crear vacío y armar el plantel después, o mandar el plantel y el capitán de una vez
    (en ese caso todo se guarda en una sola transacción)."""
    model_config = _CONFIG

    nombre: str = Field(min_length=2, max_length=100)
    id_torneo: int = Field(gt=0)
    id_facultad: int = Field(gt=0)
    jugadores: list[JugadorPlantelIn] = Field(default_factory=list, max_length=10)
    ci_capitan: CI | None = None

    @model_validator(mode="after")
    def _plantel_coherente(self):
        cis = [j.ci_jugador for j in self.jugadores]
        camisetas = [j.numero_camiseta for j in self.jugadores]
        if len(set(cis)) != len(cis):
            raise ValueError("Hay jugadores repetidos en el plantel")
        if len(set(camisetas)) != len(camisetas):
            raise ValueError("Hay números de camiseta repetidos en el plantel")
        if self.ci_capitan is not None and self.ci_capitan not in cis:
            raise ValueError("El capitán debe estar en la lista de jugadores")
        return self


class EquipoPatch(BaseModel):
    """Solo nombre y capitán. La facultad y el torneo no se cambian: se borra y se crea de nuevo."""
    model_config = _CONFIG

    nombre: str | None = Field(default=None, min_length=2, max_length=100)
    ci_capitan: CI | None = None


class EquipoOut(BaseModel):
    id_equipo: int
    nombre: str
    id_torneo: int
    torneo: str
    id_facultad: int
    facultad: str
    ci_capitan: int | None
    capitan: str | None
    cantidad_jugadores: int