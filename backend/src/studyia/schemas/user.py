from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from studyia.models import User


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    """Todos los campos son opcionales: solo se cambia lo que se envía."""

    name: str | None = Field(default=None, min_length=2, max_length=120)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    # Obligatoria cuando el usuario cambia su propia contraseña
    current_password: str | None = None
    # Solo un admin puede cambiar el rol o desactivar una cuenta
    rol: str | None = None
    is_active: bool | None = None


class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    rol: str | None = None
    is_active: bool
    created_at: datetime

    @classmethod
    def from_user(cls, user: User) -> "UserRead":
        return cls(
            id=user.id,
            name=user.name,
            email=user.email,
            rol=user.role.nombre if user.role else None,
            is_active=user.is_active,
            created_at=user.created_at,
        )


class UserList(BaseModel):
    total: int
    items: list[UserRead]
