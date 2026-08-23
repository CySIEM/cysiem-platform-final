"""Event payload shapes published onto the message bus (Kafka)."""
from datetime import datetime, timezone
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class EntityExtractedEvent(BaseModel):
    event_type: str = "entity.extracted"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    entities: List[Dict[str, Any]]


class IOCMatchedEvent(BaseModel):
    event_type: str = "ioc.matched"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    iocs: List[Dict[str, Any]]
