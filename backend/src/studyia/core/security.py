from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt
from pwdlib import PasswordHash

from studyia.core.config import settings


password_hash = PasswordHash.recommended()  # argon2

TokenType = Literal["access", "refresh"]

# Hash de relleno: si el email no existe se verifica contra él igualmente,
# así el login tarda lo mismo y no revela qué emails están registrados.
DUMMY_HASH = password_hash.hash("contraseña-de-relleno")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def _create_token(subject: str | int, token_type: TokenType, expires: timedelta) -> str:
    payload = {
        "sub": str(subject),
        "type": token_type,
        "exp": datetime.now(timezone.utc) + expires,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(subject: str | int) -> str:
    return _create_token(
        subject, "access", timedelta(minutes=settings.access_token_expire_minutes)
    )


def create_refresh_token(subject: str | int) -> str:
    return _create_token(
        subject, "refresh", timedelta(days=settings.refresh_token_expire_days)
    )


def decode_token(token: str, expected_type: TokenType) -> int:
    """Devuelve el id del usuario del token.

    Lanza jwt.InvalidTokenError si el token es inválido, expiró o es de otro tipo
    (un refresh token no sirve como access token, ni al revés).
    """
    payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
        options={"require": ["sub", "exp", "type"]},
    )
    if payload["type"] != expected_type:
        raise jwt.InvalidTokenError("Tipo de token incorrecto")
    try:
        return int(payload["sub"])
    except ValueError as error:
        raise jwt.InvalidTokenError("Subject inválido") from error
