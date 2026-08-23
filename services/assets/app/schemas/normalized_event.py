"""Contract for the normalized event JSON handed off by Team 1 (Layers 1-2)
into Layer 3. Modeled directly off real sample output (auditd + Windows
eventlog, OCSF-flavored envelope). All nested models use extra="allow" so
new fields Team 1 adds later don't break ingestion - only the fields Layer 3
actually reads are declared explicitly.
"""
from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict


class SourceInfo(BaseModel):
    model_config = ConfigDict(extra="allow")

    tenant_id: Optional[str] = None
    host: Optional[str] = None
    ip: Optional[str] = None
    segment: Optional[str] = None
    source_type: Optional[str] = None
    log_type: Optional[str] = None
    collector: Optional[str] = None


class NormalizedFields(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_category: Optional[str] = None
    action: Optional[str] = None
    user: Optional[str] = None
    process_name: Optional[str] = None
    parent_process: Optional[str] = None
    src_ip: Optional[str] = None
    src_port: Optional[int] = None
    dest_ip: Optional[str] = None
    dest_port: Optional[int] = None
    protocol: Optional[str] = None
    outcome: Optional[str] = None
    message: Optional[str] = None


class AssetExtension(BaseModel):
    model_config = ConfigDict(extra="allow")

    host: Optional[str] = None
    criticality: Optional[str] = None
    owner: Optional[str] = None
    asset_type: Optional[str] = None
    segment: Optional[str] = None
    tags: List[str] = []
    notes: Optional[str] = None


class EventExtensions(BaseModel):
    model_config = ConfigDict(extra="allow")

    asset: Optional[AssetExtension] = None


class NormalizedEvent(BaseModel):
    """One event as produced by Team 1's normalization pipeline (Layer 2)."""

    model_config = ConfigDict(extra="allow")

    event_id: Optional[str] = None
    ingested_at: Optional[str] = None
    event_time: Optional[str] = None
    source: SourceInfo = SourceInfo()
    normalized: NormalizedFields = NormalizedFields()
    ocsf_class: Optional[str] = None
    raw: Optional[str] = None
    raw_format: Optional[str] = None
    schema_version: Optional[str] = None
    extensions: Optional[EventExtensions] = None


class NormalizedEventBatch(BaseModel):
    events: List[NormalizedEvent]


class NormalizedIngestResult(BaseModel):
    events_processed: int
    entities_found: int
    assets_resolved: int
    iocs_evaluated: int
    iocs_malicious: int
    vulnerabilities: int
    failed_auth_events: int
    errors: List[str] = []
