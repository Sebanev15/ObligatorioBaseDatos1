from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
import hashlib, hmac

from .config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()




def verify_password(password: str, hashed: str) -> bool:
    calculado = hashlib.sha256(password.encode()).hexdigest()
    return hmac.compare_digest(calculado, hashed)


def create_token(correo: str, rol: str) -> str:
    payload = {
        "sub": correo,
        "rol": rol,
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")