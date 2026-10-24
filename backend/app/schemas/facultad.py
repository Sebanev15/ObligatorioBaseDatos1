from pydantic import BaseModel, ConfigDict, Field


class FacultadCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    nombre: str = Field(min_length=2, max_length=150)


class FacultadPut(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    nombre: str = Field(min_length=2, max_length=150)


class FacultadOut(BaseModel):
    id_facultad: int
    nombre: str