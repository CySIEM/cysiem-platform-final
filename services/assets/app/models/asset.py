"""Discovered/resolved asset (a host, device, or user) - the result of
entity resolution merging multiple raw entities into one logical asset.
"""
from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Asset(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "assets"

    asset_type: Mapped[str] = mapped_column(String(32), nullable=False)  # host, device, user
    primary_identifier: Mapped[str] = mapped_column(String(256), nullable=False)
    hostname: Mapped[str] = mapped_column(String(256), nullable=True)
    ip_addresses: Mapped[list] = mapped_column(JSON, default=list)
    mac_addresses: Mapped[list] = mapped_column(JSON, default=list)
    usernames: Mapped[list] = mapped_column(JSON, default=list)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    risk_score: Mapped[int] = mapped_column(default=0)
    severity: Mapped[str] = mapped_column(String(16), default="low")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    # Running counters fed by normalized-event ingestion, consumed by
    # RiskScoringService - previously these risk factors existed in
    # risk_engine.py but nothing populated them from real events.
    failed_auth_count: Mapped[int] = mapped_column(default=0)
    unusual_process_count: Mapped[int] = mapped_column(default=0)
