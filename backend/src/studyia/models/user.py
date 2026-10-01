from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Identity, Text, func, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from studyia.database.base import Base
from studyia.models.role import RoleName


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    email: Mapped[str] = mapped_column(Text, unique=True, index=True)
    # Guarda el hash (argon2), nunca la contraseña en texto plano
    password: Mapped[str] = mapped_column(Text)
    rol_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("roles.id", ondelete="SET NULL")
    )
    # Una cuenta desactivada no puede iniciar sesión ni usar tokens ya emitidos
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=true(), default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    role: Mapped["Role | None"] = relationship(back_populates="users")  # noqa: F821

    @property
    def is_admin(self) -> bool:
        return self.role is not None and self.role.nombre == RoleName.ADMIN
