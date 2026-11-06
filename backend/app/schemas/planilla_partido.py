from pydantic import BaseModel, ConfigDict, Field

_CONFIG = ConfigDict(extra="forbid")


class PlanillaPartidoCreate(BaseModel):
    model_config = _CONFIG

    ci_jugador: int = Field(ge=1_000_000, le=99_999_999)
    id_equipo: int = Field(gt=0)


class PlanillaPartidoOut(BaseModel):
    id_partido: int
    ci_jugador: int
    id_equipo: int
    jugador: str
    equipo: str
