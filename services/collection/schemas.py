"""Mirrors services/assets's NormalizedEvent contract (app/schemas/normalized_event.py)
so this service's output is guaranteed to deserialize on the receiving end.
Kept as a plain-dict builder rather than importing across services, since the
two are independently deployable and shouldn't share a Python import path.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def new_event_id() -> str:
    return str(uuid.uuid4())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_normalized_event(
    *,
    source_type: str,
    log_type: str,
    host: Optional[str] = None,
    ip: Optional[str] = None,
    tenant_id: str = "default",
    event_time: Optional[str] = None,
    ocsf_class: Optional[str] = None,
    raw: str,
    raw_format: str,
    normalized_fields: Dict[str, Any],
) -> Dict[str, Any]:
    """Assembles one event exactly matching NormalizedEvent in
    services/assets/app/schemas/normalized_event.py."""
    return {
        "event_id": new_event_id(),
        "ingested_at": now_iso(),
        "event_time": event_time or now_iso(),
        "source": {
            "tenant_id": tenant_id,
            "host": host,
            "ip": ip,
            "source_type": source_type,
            "log_type": log_type,
            "collector": "cysiem-collection-service",
        },
        "normalized": {k: v for k, v in normalized_fields.items() if v is not None},
        "ocsf_class": ocsf_class,
        "raw": raw,
        "raw_format": raw_format,
        "schema_version": "1.0",
    }
