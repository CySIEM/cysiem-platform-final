"""Historical risk score snapshot for an asset (time series for Layer 9)."""
from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RiskScore(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "risk_scores"

    asset_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    score: Mapped[int] = mapped_column(nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    factors: Mapped[dict] = mapped_column(JSON, default=dict)
