from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

TipoJugador = Literal["grado", "posgrado", "docente", "funcionario"]

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


def _validar_nacimiento(v: date | None) -> date | None:
    if v is not None and not (date(1920, 1, 1) <= v < date.today()):
        raise ValueError("La fecha de nacimiento no es válida")
    return v


class JugadorCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    ci: int = Field(ge=1_000_000, le=99_999_999, description="Sin puntos ni guion")
    nombre: str = Field(min_length=1, max_length=100)
    apellido: str = Field(min_length=1, max_length=100)
    email: str = Field(pattern=EMAIL_PATTERN, max_length=255)
    fecha_nacimiento: date
    id_facultad: int = Field(gt=0)
    tipo: TipoJugador

    _nacimiento = field_validator("fecha_nacimiento")(_validar_nacimiento)


class JugadorPatch(BaseModel):
    """Todos los campos son opcionales. La CI (clave primaria) no se puede modificar."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    apellido: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(default=None, pattern=EMAIL_PATTERN, max_length=255)
    fecha_nacimiento: date | None = None
    id_facultad: int | None = Field(default=None, gt=0)
    tipo: TipoJugador | None = None

    _nacimiento = field_validator("fecha_nacimiento")(_validar_nacimiento)


class JugadorOut(BaseModel):
    ci: int
    nombre: str
    apellido: str
    email: str
    fecha_nacimiento: date
    id_facultad: int
    facultad: str
    tipo: TipoJugador