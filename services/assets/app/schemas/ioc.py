from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class IOCBase(BaseModel):
    ioc_type: str
    value: str
    source: str = "local"
    confidence: float = 0.5
    is_malicious: bool = False
    description: str | None = None


class IOCCreate(IOCBase):
    pass


class IOCRead(IOCBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
