from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from studyia.core.security import hash_password, verify_password
from studyia.models import Role, User
from studyia.schemas.user import UserCreate, UserRead


DEFAULT_ROLE = "estudiante"
ADMIN_ROLE = "admin"


class EmailAlreadyRegistered(Exception):
    pass


class RoleNotFound(Exception):
    pass


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


def register_user(db: Session, data: UserCreate) -> User:
    if get_user_by_email(db, data.email):
        raise EmailAlreadyRegistered(data.email)

    role = get_role_by_name(db, DEFAULT_ROLE)
    user = User(
        name=data.name.strip(),
        email=data.email.lower(),
        password=hash_password(data.password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if user is None or not verify_password(password, user.password):
        return None
    return user


def to_user_read(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        name=user.name,
        email=user.email,
        rol=user.role.nombre if user.role else None,
    )
