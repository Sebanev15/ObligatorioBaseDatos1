from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Superficie = Literal["sintetico", "parquet"]

Departamento = Literal[
    "Artigas", "Canelones", "Cerro Largo", "Colonia", "Durazno", "Flores", "Florida",
    "Lavalleja", "Maldonado", "Montevideo", "Paysandú", "Río Negro", "Rivera", "Rocha",
    "Salto", "San José", "Soriano", "Tacuarembó", "Treinta y Tres",
]

_CONFIG = ConfigDict(str_strip_whitespace=True, extra="forbid")


# ---- Complejo -------------------------------------------------------------------------
class ComplejoCreate(BaseModel):
    model_config = _CONFIG

    nombre: str = Field(min_length=1, max_length=150)
    direccion: str = Field(min_length=1, max_length=255)
    departamento: Departamento


class ComplejoPatch(BaseModel):
    model_config = _CONFIG

    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    direccion: str | None = Field(default=None, min_length=1, max_length=255)
    departamento: Departamento | None = None


class ComplejoOut(BaseModel):
    id_complejo: int
    nombre: str
    direccion: str
    departamento: str


# ---- Cancha (el id_complejo viaja en la URL, no en el cuerpo) ---------------------------
class CanchaCreate(BaseModel):
    model_config = _CONFIG

    nombre_cancha: str = Field(min_length=1, max_length=100)
    superficie: Superficie
    techada: bool = False


class CanchaPatch(BaseModel):
    """El nombre es parte de la clave primaria: no se modifica."""
    model_config = _CONFIG

    superficie: Superficie | None = None
    techada: bool | None = None


class CanchaOut(BaseModel):
    nombre_cancha: str
    id_complejo: int
    superficie: Superficie
    techada: bool