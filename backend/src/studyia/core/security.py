from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from studyia.core.config import settings


password_hash = PasswordHash.recommended()  # argon2


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def create_access_token(subject: str | int, extra: dict | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": str(subject), "exp": expire, **(extra or {})}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict:
    """Lanza jwt.InvalidTokenError si el token es inválido o expiró."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
