from pydantic import BaseModel, ConfigDict, Field

_CONFIG = ConfigDict(extra="forbid")


class GolCreate(BaseModel):
    model_config = _CONFIG

    ci_jugador: int = Field(ge=1_000_000, le=99_999_999)
    minuto: int = Field(ge=0, le=130)
    autogol: bool = False


class GolPatch(BaseModel):
    model_config = _CONFIG

    minuto: int | None = Field(default=None, ge=0, le=130)
    autogol: bool | None = None


class GolOut(BaseModel):
    id_gol: int
    id_partido: int
    ci_jugador: int
    jugador: str
    id_equipo: int
    equipo: str
    minuto: int
    autogol: bool
