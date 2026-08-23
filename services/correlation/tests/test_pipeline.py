import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from correlation.normalize import normalize_alerts
from enrichment.pipeline import enrich_alerts
from investigation.attack_graph import build_attack_graph


def test_normalize_alerts_standardizes_keys():
    alerts = [
        {
            "title": "Failed login",
            "host": "server-01",
            "severity": "High",
            "timestamp": "2026-08-01T10:00:00Z",
        }
    ]

    normalized = normalize_alerts(alerts)

    assert normalized[0]["target"] == "server-01"
    assert normalized[0]["severity"] == "high"
    assert normalized[0]["title"] == "Failed login"


def test_enrich_alerts_adds_context_layers():
    alerts = [
        {"title": "Failed login from PowerShell", "target": "server-01", "source": "windows"}
    ]

    enriched = enrich_alerts(alerts)

    assert enriched[0]["threat_intelligence"]["techniques"]
    assert enriched[0]["asset_context"]["asset_type"] == "server"
    assert enriched[0]["vulnerability_context"]["risk_level"] in {"low", "medium", "high"}


def test_build_attack_graph_creates_attack_path():
    alerts = [{"title": "Failed login", "target": "server-01", "source_ip": "10.0.0.5", "username": "alice"}]

    graph = build_attack_graph(alerts)

    assert graph["summary"]
    assert "server-01" in graph["nodes"]
    assert "10.0.0.5" in graph["nodes"]
    assert len(graph["edges"]) >= 1
