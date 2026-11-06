from pydantic import BaseModel


class PartidoEquipoOut(BaseModel):
    id_partido: int
    id_equipo: int
    id_torneo: int
    equipo: str
