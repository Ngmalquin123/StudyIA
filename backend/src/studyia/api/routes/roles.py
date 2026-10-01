from fastapi import APIRouter
from sqlalchemy import select

from studyia.api.deps import CurrentUser, DbSession
from studyia.models import Role
from studyia.schemas.role import RoleRead


router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("", response_model=list[RoleRead])
def list_roles(db: DbSession, current_user: CurrentUser):
    return list(db.scalars(select(Role).order_by(Role.id)))
