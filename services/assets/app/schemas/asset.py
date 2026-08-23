from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AssetBase(BaseModel):
    asset_type: str
    primary_identifier: str
    hostname: str | None = None
    ip_addresses: list[str] = []
    mac_addresses: list[str] = []
    usernames: list[str] = []
    tags: list[str] = []


class AssetCreate(AssetBase):
    pass


class AssetRead(AssetBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    risk_score: int
    severity: str
    failed_auth_count: int = 0
    unusual_process_count: int = 0
    created_at: datetime
    updated_at: datetime
