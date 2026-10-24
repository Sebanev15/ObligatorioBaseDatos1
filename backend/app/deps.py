"""STUB TEMPORAL: lo reemplaza la autenticación real (JWT) del módulo de login.

Contrato que usan los routers: AnyUser, AdminUser y PlanilleroOrAdmin devuelven un objeto
con el atributo `rol` ("administrador" | "planillero"), que se usa para elegir la conexión a MySQL.
"""
from typing import Annotated

from fastapi import Depends
from pydantic import BaseModel


class CurrentUser(BaseModel):
    correo: str
    rol: str


def _usuario_de_desarrollo() -> CurrentUser:
    return CurrentUser(correo="dev@local", rol="administrador")


AnyUser = Annotated[CurrentUser, Depends(_usuario_de_desarrollo)]
AdminUser = AnyUser
PlanilleroOrAdmin = AnyUser