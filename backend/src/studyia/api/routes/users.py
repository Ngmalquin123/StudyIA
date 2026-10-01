from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from studyia.api.deps import CurrentAdmin, CurrentUser, DbSession, is_admin
from studyia.models import User
from studyia.schemas.user import UserList, UserRead, UserUpdate
from studyia.services import user_service
from studyia.services.auth_service import (
    EmailAlreadyRegistered,
    RoleNotFound,
    get_user_by_id,
    to_user_read,
)


router = APIRouter(prefix="/users", tags=["Usuarios"])


def get_user_or_404(db: DbSession, user_id: int) -> User:
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    return user


def ensure_owner_or_admin(current_user: User, target: User) -> None:
    """Cada usuario solo puede modificar su propia cuenta; un admin, cualquiera."""
    if current_user.id != target.id and not is_admin(current_user):
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
        items=[to_user_read(user) for user in users],
    )


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: DbSession, admin: CurrentAdmin):
    """Ver un usuario por id. Solo admin (el estudiante usa /api/auth/me)."""
    return to_user_read(get_user_or_404(db, user_id))


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int, data: UserUpdate, db: DbSession, current_user: CurrentUser
):
    """Edita nombre, email, contraseña y/o rol. Solo se cambian los campos enviados.

    El rol solo lo puede cambiar un admin, y nunca el suyo propio
    (así el sistema no se queda sin administradores por error).
    """
    user = get_user_or_404(db, user_id)
    ensure_owner_or_admin(current_user, user)

    if data.rol is not None:
        if not is_admin(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo un administrador puede cambiar roles",
            )
        if user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes cambiar tu propio rol",
            )

    try:
        user = user_service.update_user(db, user, data)
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
    return to_user_read(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: DbSession, current_user: CurrentUser):
    """Elimina la cuenta y, en cascada, su progreso y actividades."""
    user = get_user_or_404(db, user_id)
    ensure_owner_or_admin(current_user, user)
    user_service.delete_user(db, user)
