"""Persisted relationship edge between two entities (mirrors the in-memory
graph in app/core/graph_engine.py for durability and audit purposes).
"""
from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EntityEdge(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "entity_edges"

    src_entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    src_value: Mapped[str] = mapped_column(String(512), nullable=False)
    dst_entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    dst_value: Mapped[str] = mapped_column(String(512), nullable=False)
    edge_type: Mapped[str] = mapped_column(String(64), nullable=False)
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)
