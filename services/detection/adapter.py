"""Maps a detection result back onto the event it came from, into the raw
alert-dict shape services/correlation's POST /ingest actually expects
(read directly from correlation/normalize.py, correlation/facts.py,
correlation/severity.py, enrichment/pipeline.py - there is no formal
Pydantic schema on that side, just these field names).

Title text matters beyond display: correlation's own MITRE mapping and
root-cause logic keyword-match on it (e.g. "failed login" -> T1110). This
builds the title from the underlying event's own fields (evidence-based,
matching that team's own design) rather than inventing wording purely
from the model's output.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List


def _build_title(event: Dict[str, Any], detection: Dict[str, Any]) -> str:
    normalized = event.get("normalized", {})
    action = (normalized.get("action") or "").lower()
    outcome = (normalized.get("outcome") or "").lower()

    if action == "ssh_login" and outcome == "failure":
        return "Failed login from " + str(normalized.get("src_ip") or "unknown source")
    if action == "ssh_login" and outcome == "success":
        return "Successful login from " + str(normalized.get("src_ip") or "unknown source")
    if "powershell" in str(normalized.get("process_name") or "").lower():
        return "Suspicious PowerShell process execution"
    if normalized.get("process_name"):
        return f"Suspicious process execution: {normalized['process_name']}"

    return detection.get("reason") or "Detected security event"


def build_correlation_alert(event: Dict[str, Any], detection: Dict[str, Any]) -> Dict[str, Any]:
    normalized = event.get("normalized", {})
    source = event.get("source", {})

    return {
        "id": event.get("event_id") or str(uuid.uuid4()),
        "source": source.get("log_type") or source.get("source_type") or "unknown",
        "host": source.get("host"),
        "target": source.get("host"),
        "timestamp": event.get("event_time") or datetime.now(timezone.utc).isoformat(),
        "title": _build_title(event, detection),
        "severity": detection.get("severity", "medium"),
        "username": normalized.get("user"),
        "source_ip": normalized.get("src_ip"),
        "destination_ip": normalized.get("dest_ip"),
        "process_name": normalized.get("process_name"),
        "cves": [],
        "asset_criticality": (event.get("extensions") or {}).get("asset", {}).get("criticality", "medium"),
        "mitre": {"technique": detection.get("mitre")} if detection.get("mitre") else None,
        "ai_detection": {
            "prediction": detection.get("prediction"),
            "confidence": detection.get("confidence"),
            "reason": detection.get("reason"),
        },
    }


def build_layer4_output(
    event: Dict[str, Any], detection: Dict[str, Any], entities: List[Any], evidence: List[Any]
) -> Dict[str, Any]:
    """The documented Layer 4 -> Layer 5 contract:
    {detection, severity, confidence, entities, evidence}."""
    return {
        "detection": {
            "prediction": detection.get("prediction"),
            "mitre": detection.get("mitre"),
            "reason": detection.get("reason"),
        },
        "severity": detection.get("severity"),
        "confidence": detection.get("confidence"),
        "entities": entities,
        "evidence": evidence,
    }
