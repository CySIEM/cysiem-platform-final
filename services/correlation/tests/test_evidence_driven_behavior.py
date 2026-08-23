import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.incident_api import analyze_incidents
from investigation.attack_graph import build_attack_graph


def test_attack_graph_uses_only_observed_entities():
    alerts = [
        {"title": "Failed login", "target": "server-01", "source_ip": "10.0.0.5", "username": "alice"}
    ]

    graph = build_attack_graph(alerts)

    assert "server-01" in graph["nodes"]
    assert "10.0.0.5" in graph["nodes"]
    assert "alice" in graph["nodes"]
    assert all(node not in {"unknown", "Initial Access"} for node in graph["nodes"])


def test_analyze_incidents_returns_structured_unclassified_mitre_when_no_supporting_evidence():
    alerts = [{"title": "Generic alert", "target": "server-01"}]

    result = analyze_incidents(alerts)
    incident = result["incidents"][0]

    assert incident["mitre"][0]["name"] == "Unclassified"
    assert incident["mitre"][0]["status"] == "insufficient evidence"
