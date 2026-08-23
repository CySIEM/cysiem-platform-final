import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api import server as api_server
from api.incident_api import analyze_incidents
from correlation.correlate import correlate_alerts
from correlation.deduplicate import deduplicate_alerts
from correlation.normalize import normalize_alerts
from correlation.severity import calculate_confidence, calculate_severity
from enrichment.pipeline import enrich_alerts
from investigation.attack_graph import build_attack_graph
from investigation.root_cause import suggest_root_cause


def test_deduplicate_alerts_removes_duplicates():
    alerts = [
        {"id": "a1", "source": "windows", "target": "server-01", "timestamp": "2026-08-01T10:00:00Z", "title": "Failed login"},
        {"id": "a1", "source": "windows", "target": "server-01", "timestamp": "2026-08-01T10:00:00Z", "title": "Failed login"},
        {"id": "a2", "source": "linux", "target": "server-02", "timestamp": "2026-08-01T10:05:00Z", "title": "Suspicious process"},
    ]

    result = deduplicate_alerts(alerts)

    assert len(result) == 2
    assert result[0]["id"] == "a1"


def test_correlate_alerts_groups_related_events():
    alerts = [
        {"id": "a1", "source": "windows", "target": "server-01", "timestamp": "2026-08-01T10:00:00Z", "title": "Failed login"},
        {"id": "a2", "source": "windows", "target": "server-01", "timestamp": "2026-08-01T10:03:00Z", "title": "Failed login"},
        {"id": "a3", "source": "linux", "target": "server-02", "timestamp": "2026-08-01T10:10:00Z", "title": "Suspicious process"},
    ]

    incidents = correlate_alerts(alerts)

    assert len(incidents) == 2
    assert incidents[0]["alerts"][0]["id"] == "a1"


def test_calculate_severity_returns_score():
    alerts = [
        {"severity": "high"},
        {"severity": "medium"},
        {"severity": "low"},
    ]

    score = calculate_severity(alerts)

    assert score >= 50


def test_deduplicate_alerts_uses_content_when_id_is_missing():
    alerts = [
        {"source": "windows", "target": "server-01", "timestamp": "2026-08-01T10:00:00Z", "title": "Failed login"},
        {"source": "windows", "target": "server-01", "timestamp": "2026-08-01T10:00:00Z", "title": "Failed login"},
    ]

    result = deduplicate_alerts(alerts)

    assert len(result) == 1


def test_calculate_severity_handles_missing_and_numeric_values():
    alerts = [
        {"severity": 90},
        {},
        {"severity": "critical"},
    ]

    score = calculate_severity(alerts)

    assert score == 100


def test_normalize_alerts_enriches_target_and_severity():
    alerts = [{"title": "Failed login", "host": "server-01", "severity": "High"}]

    normalized = normalize_alerts(alerts)

    assert normalized[0]["target"] == "server-01"
    assert normalized[0]["severity"] == "high"


def test_enrich_alerts_adds_context_layers():
    alerts = [{"title": "PowerShell execution", "target": "server-01"}]

    enriched = enrich_alerts(alerts)

    assert enriched[0]["threat_intelligence"]["techniques"] == ["T1059", "T1055"]
    assert enriched[0]["asset_context"]["asset_type"] == "server"


def test_build_attack_graph_creates_attack_path():
    alerts = [{"title": "Failed login", "target": "server-01", "source_ip": "10.0.0.5", "username": "alice"}]

    graph = build_attack_graph(alerts)

    assert "server-01" in graph["nodes"]
    assert "10.0.0.5" in graph["nodes"]
    assert len(graph["edges"]) >= 1


def test_global_attack_graph_has_no_inferred_edges_for_unrelated_alerts():
    alerts = [
        {"title": "Failed login", "target": "server-01", "source_ip": "10.0.0.5", "username": "alice"},
        {"title": "Suspicious process", "target": "server-02", "source_ip": "10.0.0.6", "username": "bob"},
    ]

    graph = build_attack_graph(alerts)

    assert "server-01" in graph["nodes"]
    assert "server-02" in graph["nodes"]
    assert ("server-01", "server-02") not in graph["edges"]
    assert ("server-02", "server-01") not in graph["edges"]


def test_confidence_scoring_is_explainable():
    alerts = [{"title": "Failed login", "source_ip": "10.0.0.5", "username": "alice"}]

    confidence = calculate_confidence(alerts)

    assert confidence["score"] >= 40
    assert confidence["reasons"]


def test_root_cause_is_evidence_based():
    alerts = [{"title": "Failed login", "username": "alice"}]

    root_cause = suggest_root_cause(alerts)

    assert "Failed login activity" in root_cause["attack_chain"]
    assert root_cause["recommendations"]


def test_correlation_reasons_are_specific_and_evidence_based():
    alerts = [
        {"target": "server-01", "host": "server-01", "username": "alice", "source_ip": "10.0.0.5", "timestamp": "2026-08-01T10:00:00Z"},
        {"target": "server-01", "host": "server-01", "username": "alice", "source_ip": "10.0.0.5", "timestamp": "2026-08-01T10:02:00Z"},
    ]

    incidents = correlate_alerts(alerts)

    assert any("same host" in reason.lower() or "same user" in reason.lower() or "same ip" in reason.lower() for reason in incidents[0]["correlation_reasons"])


def test_facts_are_deduplicated_without_losing_alerts():
    alerts = [
        {"target": "server-01", "host": "server-01", "username": "alice", "source_ip": "10.0.0.5", "process_name": "cmd.exe"},
        {"target": "server-01", "host": "server-01", "username": "alice", "source_ip": "10.0.0.5", "process_name": "cmd.exe"},
    ]

    facts = correlate_alerts(alerts)[0]["facts"]

    assert facts["hosts"] == ["server-01"]
    assert facts["users"] == ["alice"]
    assert facts["ips"] == ["10.0.0.5"]
    assert len(correlate_alerts(alerts)[0]["alerts"]) == 2


def test_incident_attack_graph_uses_only_incident_alerts():
    alerts = [
        {"id": "a1", "source": "windows", "target": "server-01", "timestamp": "2026-08-01T10:00:00Z", "title": "Failed login"},
        {"id": "a2", "source": "windows", "target": "server-01", "timestamp": "2026-08-01T10:03:00Z", "title": "Failed login"},
        {"id": "a3", "source": "linux", "target": "server-02", "timestamp": "2026-08-01T10:10:00Z", "title": "Suspicious process"},
    ]

    result = analyze_incidents(alerts)
    incident_one = result["incidents"][0]
    incident_two = result["incidents"][1]

    assert "server-01" in incident_one["attack_graph"]["nodes"]
    assert "server-02" not in incident_one["attack_graph"]["nodes"]

    assert "server-02" in incident_two["attack_graph"]["nodes"]
    assert "server-01" not in incident_two["attack_graph"]["nodes"]


def test_timeline_endpoint_uses_incident_specific_timeline(monkeypatch):
    incident = {
        "incident_id": "INC-002",
        "alerts": [{"id": "a1"}, {"id": "a2"}, {"id": "a3"}],
        "timeline": [{"id": "a3"}],
    }

    monkeypatch.setattr(api_server, "list_incidents", lambda: [incident])

    assert api_server.get_timeline("INC-002") == [{"id": "a3"}]
