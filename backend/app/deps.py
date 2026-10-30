from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from pydantic import BaseModel

from .config import settings

bearer = HTTPBearer()


class CurrentUser(BaseModel):
    correo: str
    rol: str


def _usuario_actual(creds=Depends(bearer)) -> CurrentUser:
    try:
        data = jwt.decode(creds.credentials, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido o vencido")
    return CurrentUser(correo=data["sub"], rol=data["rol"])


def _solo_admin(user: CurrentUser = Depends(_usuario_actual)) -> CurrentUser:
    if user.rol != "administrador":
        raise HTTPException(status_code=403, detail="No autorizado")
    return user


def _planillero_o_admin(user: CurrentUser = Depends(_usuario_actual)) -> CurrentUser:
    if user.rol not in ("administrador", "planillero"):
        raise HTTPException(status_code=403, detail="No autorizado")
    return user


AnyUser = Annotated[CurrentUser, Depends(_usuario_actual)]
AdminUser = Annotated[CurrentUser, Depends(_solo_admin)]
PlanilleroOrAdmin = Annotated[CurrentUser, Depends(_planillero_o_admin)]