from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from studyia.core.security import hash_password
from studyia.models import User
from studyia.schemas.user import UserUpdate
from studyia.services.auth_service import (
    EmailAlreadyRegistered,
    get_role_by_name,
    get_user_by_email,
)


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


def update_user(db: Session, user: User, data: UserUpdate) -> User:
    if data.email is not None:
        email = data.email.lower()
        existing = get_user_by_email(db, email)
        if existing is not None and existing.id != user.id:
            raise EmailAlreadyRegistered(email)
        user.email = email

    if data.name is not None:
        user.name = data.name.strip()

    if data.password is not None:
        user.password = hash_password(data.password)

    if data.rol is not None:
        user.role = get_role_by_name(db, data.rol)

    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()
