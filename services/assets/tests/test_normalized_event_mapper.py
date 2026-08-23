"""Pure-logic tests for app/core/normalized_event_mapper.py using event
shapes taken directly from real Team 1 export samples (auditd + Windows
eventlog) - no database required.
"""
from app.core.constants import EntityType
from app.core.normalized_event_mapper import build_asset_context, extract_entities, is_failed_event
from app.schemas.normalized_event import NormalizedEvent

LINUX_EVENT = {
    "event_id": "346d3ad1-decf-4c10-a5ec-7c66be86912b",
    "source": {
        "host": "debian13-srv01",
        "ip": "192.168.30.30",
        "segment": "OPT2",
        "source_type": "linux_server",
        "log_type": "auditd",
        "collector": "fluent-bit",
    },
    "normalized": {
        "event_category": "process",
        "action": "process_execution",
        "user": "0",
        "process_name": "date",
        "outcome": None,
        "message": "EXECVE argv: date",
    },
    "raw": "type=EXECVE msg=audit(1786174449.546:1499): argc=1 a0=\"date\"",
    "extensions": {
        "asset": {
            "host": "debian13-srv01",
            "criticality": "high",
            "owner": "you",
            "asset_type": "linux_server",
            "segment": "OPT2",
            "tags": [],
            "notes": "MAC 00:0c:29:c1:57:a5, IP 192.168.30.30",
        }
    },
}

WINDOWS_FAILURE_EVENT = {
    "event_id": "1f58b271-f829-4ceb-8be6-1659e23638e7",
    "source": {
        "host": "debian13-srv01",
        "ip": "192.168.30.30",
        "source_type": "linux_server",
        "log_type": "auditd",
    },
    "normalized": {
        "event_category": "other",
        "action": "usys_config",
        "user": "0",
        "process_name": "/usr/sbin/NetworkManager",
        "outcome": "failure",
        "message": "op=sleep-control result=fail res=failed",
    },
    "extensions": {"asset": {"notes": "MAC 00:0c:29:c1:57:a5, IP 192.168.30.30"}},
}


def test_extracts_hostname_ip_process_from_structured_fields():
    event = NormalizedEvent.model_validate(LINUX_EVENT)
    entities = extract_entities(event)
    values_by_type = {}
    for e in entities:
        values_by_type.setdefault(e.entity_type, set()).add(e.value)

    assert "debian13-srv01" in values_by_type[EntityType.HOSTNAME]
    assert "192.168.30.30" in values_by_type[EntityType.IP_ADDRESS]
    assert "date" in values_by_type[EntityType.PROCESS]


def test_extracts_mac_from_asset_notes_free_text():
    event = NormalizedEvent.model_validate(LINUX_EVENT)
    entities = extract_entities(event)
    macs = [e.value for e in entities if e.entity_type == EntityType.MAC_ADDRESS]
    assert "00:0c:29:c1:57:a5" in macs


def test_numeric_uid_not_treated_as_username():
    # normalized.user == "0" is a raw uid, not a real username - must not
    # pollute the username entity pool.
    event = NormalizedEvent.model_validate(LINUX_EVENT)
    entities = extract_entities(event)
    usernames = [e.value for e in entities if e.entity_type == EntityType.USERNAME]
    assert "0" not in usernames


def test_build_asset_context_merges_structured_and_notes():
    event = NormalizedEvent.model_validate(LINUX_EVENT)
    ctx = build_asset_context(event)
    assert ctx["hostname"] == "debian13-srv01"
    assert "192.168.30.30" in ctx["ip_addresses"]
    assert "00:0c:29:c1:57:a5" in ctx["mac_addresses"]
    assert "linux_server" in ctx["tags"]
    assert ctx["metadata_json"]["criticality"] == "high"


def test_is_failed_event_detects_structured_outcome():
    event = NormalizedEvent.model_validate(WINDOWS_FAILURE_EVENT)
    assert is_failed_event(event) is True


def test_is_failed_event_false_for_success():
    event = NormalizedEvent.model_validate(LINUX_EVENT)
    assert is_failed_event(event) is False
