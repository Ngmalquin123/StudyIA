from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from studyia.core.exceptions import (
    EmailAlreadyRegistered,
    InvalidCurrentPassword,
    RoleNotFound,
)
from studyia.core.security import hash_password, verify_password
from studyia.models import Role, User
from studyia.schemas.user import UserUpdate


def get_role_by_name(db: Session, nombre: str) -> Role:
    role = db.scalar(select(Role).where(Role.nombre == nombre.lower()))
    if role is None:
        raise RoleNotFound(nombre)
    return role


def get_user_by_email(db: Session, email: str) -> User | None:
    stmt = (
        select(User)
        .options(joinedload(User.role))
        .where(User.email == email.lower())
    )
    return db.scalar(stmt)


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id, options=[joinedload(User.role)])


def list_users(db: Session, skip: int = 0, limit: int = 50) -> list[User]:
    stmt = (
        select(User)
        .options(joinedload(User.role))
        .order_by(User.id)
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt))


def count_users(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(User))


def update_user(
    db: Session, user: User, data: UserUpdate, *, require_current_password: bool
) -> User:
    """Aplica solo los campos enviados.

    Los permisos (quién puede cambiar rol o is_active) los valida la ruta;
    aquí solo están las reglas de datos.
    """
    if data.email is not None:
        email = data.email.lower()
        existing = get_user_by_email(db, email)
        if existing is not None and existing.id != user.id:
            raise EmailAlreadyRegistered(email)
        user.email = email

    if data.name is not None:
        user.name = data.name.strip()

    if data.password is not None:
        if require_current_password and (
            data.current_password is None
            or not verify_password(data.current_password, user.password)
        ):
            raise InvalidCurrentPassword()
        user.password = hash_password(data.password)

    if data.rol is not None:
        user.role = get_role_by_name(db, data.rol)

    if data.is_active is not None:
        user.is_active = data.is_active

    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()
