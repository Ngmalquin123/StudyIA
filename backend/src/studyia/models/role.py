from enum import StrEnum

from sqlalchemy import BigInteger, Identity, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from studyia.database.base import Base


class RoleName(StrEnum):
    """Roles que crea la migración inicial."""

    ADMIN = "admin"
    ESTUDIANTE = "estudiante"


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    nombre: Mapped[str] = mapped_column(Text, unique=True)

    users: Mapped[list["User"]] = relationship(back_populates="role")  # noqa: F821
