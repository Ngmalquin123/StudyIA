import jwt
from sqlalchemy.orm import Session

from studyia.core.exceptions import EmailAlreadyRegistered
from studyia.core.security import (
    DUMMY_HASH,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from studyia.models import RoleName, User
from studyia.schemas.auth import Token
from studyia.schemas.user import UserCreate
from studyia.services.user_service import get_role_by_name, get_user_by_email, get_user_by_id


def register_user(db: Session, data: UserCreate) -> User:
    if get_user_by_email(db, data.email):
        raise EmailAlreadyRegistered(data.email)

    user = User(
        name=data.name.strip(),
        email=data.email.lower(),
        password=hash_password(data.password),
        role=get_role_by_name(db, RoleName.ESTUDIANTE),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User | None:
    """Devuelve el usuario si email y contraseña son correctos y la cuenta está activa."""
    user = get_user_by_email(db, email)
    if user is None:
        verify_password(password, DUMMY_HASH)  # mismo tiempo de respuesta
        return None
    if not verify_password(password, user.password) or not user.is_active:
        return None
    return user


def issue_tokens(user: User) -> Token:
    return Token(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


def get_active_user_from_token(db: Session, token: str, token_type: TokenType) -> User | None:
    try:
        user_id = decode_token(token, token_type)
    except jwt.InvalidTokenError:
        return None
    user = get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        return None
    return user
