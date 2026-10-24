
from pydantic import BaseModel, ConfigDict, Field


class InscripcionCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    ci_jugador: int = Field(
        ge=1_000_000,
        le=99_999_999,
        description="Cédula sin puntos ni guion",
    )
    numero_camiseta: int = Field(ge=1, le=99)


class InscripcionPatch(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    numero_camiseta: int | None = Field(
        default=None,
        ge=1,
        le=99,
    )


class InscripcionOut(BaseModel):
    id_equipo: int
    ci_jugador: int
    id_torneo: int
    numero_camiseta: int
    nombre: str
    apellido: str
