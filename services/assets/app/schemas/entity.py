from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EntityBase(BaseModel):
    entity_type: str
    value: str
    confidence: float = 1.0
    source_log_type: str | None = None
    context: str | None = None


class EntityCreate(EntityBase):
    pass


class EntityRead(EntityBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    occurrences: int
    created_at: datetime
    updated_at: datetime
