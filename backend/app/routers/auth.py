from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..db import fetch_one, get_connection
from ..security import create_token, verify_password

router = APIRouter(tags=["auth"])


class LoginIn(BaseModel):
    correo: str
    password: str


@router.post("/login")
def login(data: LoginIn):
    with get_connection("auth") as conn:
        user = fetch_one(
            conn,
            "SELECT correo, contrasena, rol FROM login WHERE correo = %s",
            (data.correo,),
        )
    if not user or not verify_password(data.password, user["contrasena"]):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return {
        "access_token": create_token(user["correo"], user["rol"]),
        "token_type": "bearer",
        "rol": user["rol"],
    }