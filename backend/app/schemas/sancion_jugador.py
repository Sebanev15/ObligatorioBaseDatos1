from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

# Idénticos a los valores del CHECK de la tabla (sin tildes)
MotivoSancion = Literal["roja", "acumulacion de amarillas", "disciplinaria"]

_CONFIG = ConfigDict(extra="forbid")

CI = Annotated[int, Field(ge=1_000_000, le=99_999_999)]
NumeroFecha = Annotated[int, Field(ge=1, le=50)]       # topes de cordura, no vienen del enunciado
CantidadFechas = Annotated[int, Field(ge=1, le=20)]


class SancionCreate(BaseModel):
    """Por la API solo se crean sanciones disciplinarias (por eso no se envía el motivo).
    Las de tarjeta roja y de 3 amarillas las genera el sistema automáticamente."""
    model_config = _CONFIG

    ci_jugador: CI
    id_torneo: int = Field(gt=0)
    numero_fecha_inicio: NumeroFecha
    cantidad_fechas: CantidadFechas


class SancionPatch(BaseModel):
    """Solo se pueden ajustar las fechas. Jugador, torneo y motivo no se cambian: se elimina y se crea de nuevo."""
    model_config = _CONFIG

    numero_fecha_inicio: NumeroFecha | None = None
    cantidad_fechas: CantidadFechas | None = None


class SancionOut(BaseModel):
    id_sancion: int
    ci_jugador: int
    jugador: str
    id_torneo: int
    torneo: str
    motivo: MotivoSancion
    numero_fecha_inicio: int
    cantidad_fechas: int
    numero_fecha_fin: int          # última fecha que cumple suspendido (inicio + cantidad - 1)