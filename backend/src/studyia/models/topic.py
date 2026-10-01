from sqlalchemy import BigInteger, Identity, Text
from sqlalchemy.orm import Mapped, mapped_column

from studyia.database.base import Base


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
