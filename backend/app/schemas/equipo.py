
from pydantic import BaseModel, ConfigDict, Field


class EquipoCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    nombre: str = Field(min_length=2, max_length=100)
    id_torneo: int = Field(gt=0)
    id_facultad: int = Field(gt=0)


class EquipoPatch(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    nombre: str | None = Field(default=None, min_length=2, max_length=100)
    id_facultad: int | None = Field(default=None, gt=0)

    # Puede ser null para quitar el capitán.
    ci_capitan: int | None = Field(
        default=None,
        ge=1_000_000,
        le=99_999_999,
    )


class EquipoOut(BaseModel):
    id_equipo: int
    nombre: str
    id_torneo: int
    id_facultad: int
    ci_capitan: int | None
