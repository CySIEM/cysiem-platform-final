"""Validation, cleaning and normalization glue: picks the right parser for
a raw record and turns it into the NormalizedEvent shape services/assets
expects.
"""
import json
from typing import Any, Dict, List, Optional

from parsers import parse_linux_auth_line, parse_network_flow, parse_windows_event
from schemas import build_normalized_event


def clean_line(line: str) -> str:
    """Strip control characters and surrounding whitespace; collapse
    accidental null bytes some log shippers introduce."""
    return line.replace("\x00", "").strip()


def normalize_raw_line(line: str, tenant_id: str = "default") -> Optional[Dict[str, Any]]:
    """A raw text log line -> NormalizedEvent dict, or None if the line is
    empty/unparseable garbage (validation failure - dropped, not forwarded)."""
    line = clean_line(line)
    if not line:
        return None

    parsed = parse_linux_auth_line(line)
    if parsed is None:
        # Not a recognizable structured line - still forward it as a raw,
        # minimally-normalized event rather than silently dropping data
        # Layer 3's regex fallback can still work with.
        return build_normalized_event(
            source_type="unknown",
            log_type="raw_line",
            raw=line,
            raw_format="text",
            normalized_fields={"message": line},
            tenant_id=tenant_id,
        )

    return build_normalized_event(
        source_type="linux",
        log_type="auth_log",
        host=parsed.get("host"),
        event_time=parsed.get("event_time"),
        raw=line,
        raw_format="syslog",
        normalized_fields=parsed["normalized"],
        tenant_id=tenant_id,
    )


def normalize_windows_event(event: Dict[str, Any], tenant_id: str = "default") -> Optional[Dict[str, Any]]:
    parsed = parse_windows_event(event)
    if parsed is None:
        return None
    return build_normalized_event(
        source_type="windows",
        log_type="security_eventlog",
        host=parsed.get("host"),
        ip=parsed.get("normalized", {}).get("src_ip"),
        event_time=parsed.get("event_time"),
        ocsf_class=parsed.get("ocsf_class"),
        raw=json.dumps(event),
        raw_format="json",
        normalized_fields=parsed["normalized"],
        tenant_id=tenant_id,
    )


def normalize_network_flow(flow: Dict[str, Any], tenant_id: str = "default") -> Optional[Dict[str, Any]]:
    parsed = parse_network_flow(flow)
    if parsed is None:
        return None
    return build_normalized_event(
        source_type="network",
        log_type="flow",
        host=parsed.get("host"),
        ip=parsed.get("normalized", {}).get("src_ip"),
        event_time=parsed.get("event_time"),
        ocsf_class=parsed.get("ocsf_class"),
        raw=json.dumps(flow),
        raw_format="json",
        normalized_fields=parsed["normalized"],
        tenant_id=tenant_id,
    )


def normalize_batch(records: List[str], source_type: str, tenant_id: str = "default") -> List[Dict[str, Any]]:
    """source_type: 'linux' | 'windows' | 'network'. Records are raw lines
    for 'linux', JSON strings/dicts for 'windows'/'network'."""
    events: List[Dict[str, Any]] = []
    for record in records:
        if source_type == "linux":
            event = normalize_raw_line(record, tenant_id=tenant_id)
        else:
            data = json.loads(record) if isinstance(record, str) else record
            if source_type == "windows":
                event = normalize_windows_event(data, tenant_id=tenant_id)
            elif source_type == "network":
                event = normalize_network_flow(data, tenant_id=tenant_id)
            else:
                raise ValueError(f"Unknown source_type: {source_type}")
        if event is not None:
            events.append(event)
    return events
