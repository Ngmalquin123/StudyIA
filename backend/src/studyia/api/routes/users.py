from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from studyia.api.deps import CurrentAdmin, CurrentUser, DbSession
from studyia.core.exceptions import (
    EmailAlreadyRegistered,
    InvalidCurrentPassword,
    RoleNotFound,
)
from studyia.models import User
from studyia.schemas.user import UserList, UserRead, UserUpdate
from studyia.services import user_service


router = APIRouter(prefix="/users", tags=["Usuarios"])


def get_user_or_404(db: DbSession, user_id: int) -> User:
    user = user_service.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    return user


def ensure_owner_or_admin(current_user: User, target: User) -> None:
    """Cada usuario solo puede modificar su propia cuenta; un admin, cualquiera."""
    if current_user.id != target.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso sobre este usuario",
        )


@router.get("", response_model=UserList)
def list_users(
    db: DbSession,
    admin: CurrentAdmin,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):
    """Lista los usuarios registrados. Solo admin. Paginado con skip/limit."""
    users = user_service.list_users(db, skip=skip, limit=limit)
    return UserList(
        total=user_service.count_users(db),
        items=[UserRead.from_user(user) for user in users],
    )


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: DbSession, admin: CurrentAdmin):
    """Ver un usuario por id. Solo admin (el estudiante usa /api/auth/me)."""
    return UserRead.from_user(get_user_or_404(db, user_id))


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int, data: UserUpdate, db: DbSession, current_user: CurrentUser
):
    """Edita nombre, email, contraseña, rol y/o is_active. Solo se cambian los campos enviados.

    - Para cambiar la contraseña propia hay que enviar `current_password`.
    - El rol y `is_active` solo los cambia un admin, y nunca los suyos propios
      (así el sistema no se queda sin administradores por error).
    """
    user = get_user_or_404(db, user_id)
    ensure_owner_or_admin(current_user, user)
    is_self = user.id == current_user.id

    if data.rol is not None or data.is_active is not None:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo un administrador puede cambiar roles o desactivar cuentas",
            )
        if is_self:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes cambiar tu propio rol ni desactivar tu cuenta",
            )

    try:
        user = user_service.update_user(
            db, user, data, require_current_password=is_self
        )
    except EmailAlreadyRegistered:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado",
        )
    except RoleNotFound:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El rol no existe",
        )
    except InvalidCurrentPassword:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual es incorrecta",
        )
    return UserRead.from_user(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: DbSession, current_user: CurrentUser):
    """Elimina la cuenta y, en cascada, su progreso y actividades."""
    user = get_user_or_404(db, user_id)
    ensure_owner_or_admin(current_user, user)
    if user.id == current_user.id and current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un administrador no puede eliminar su propia cuenta",
        )
    user_service.delete_user(db, user)
