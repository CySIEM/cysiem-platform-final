"""Generic extracted entity (IP, hostname, user, hash, domain, ...)."""
from sqlalchemy import Float, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Entity(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "entities"
    __table_args__ = (Index("ix_entities_type_value", "entity_type", "value", unique=True),)

    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    value: Mapped[str] = mapped_column(String(512), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    source_log_type: Mapped[str] = mapped_column(String(32), nullable=True)
    context: Mapped[str] = mapped_column(Text, nullable=True)
    occurrences: Mapped[int] = mapped_column(default=1)
