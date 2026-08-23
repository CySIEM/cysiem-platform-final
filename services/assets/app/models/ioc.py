"""Indicator of Compromise, either extracted locally or matched against a
threat intel feed (MISP / OTX) via app/integrations.
"""
from sqlalchemy import Boolean, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class IOC(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "iocs"

    ioc_type: Mapped[str] = mapped_column(String(32), nullable=False)
    value: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(64), default="local")  # local, misp, otx
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    is_malicious: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    mitre_techniques: Mapped[list] = mapped_column(Text, nullable=True)
