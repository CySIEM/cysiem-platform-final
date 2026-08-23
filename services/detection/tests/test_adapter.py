from adapter import build_correlation_alert, build_layer4_output

SAMPLE_EVENT = {
    "event_id": "evt-123",
    "event_time": "2026-08-23T10:15:02+00:00",
    "source": {"host": "server-01", "log_type": "auth_log", "source_type": "linux"},
    "normalized": {
        "action": "ssh_login",
        "outcome": "failure",
        "user": "admin",
        "src_ip": "185.220.101.5",
    },
}

SAMPLE_DETECTION = {
    "prediction": "malicious",
    "confidence": 0.85,
    "severity": "high",
    "mitre": "T1110",
    "reason": "Repeated failed SSH logins from a known-bad IP.",
}


def test_build_correlation_alert_maps_team4_fields():
    alert = build_correlation_alert(SAMPLE_EVENT, SAMPLE_DETECTION)

    assert alert["id"] == "evt-123"
    assert alert["host"] == "server-01"
    assert alert["target"] == "server-01"
    assert alert["title"] == "Failed login from 185.220.101.5"
    assert alert["severity"] == "high"
    assert alert["username"] == "admin"
    assert alert["source_ip"] == "185.220.101.5"


def test_title_triggers_correlation_services_own_mitre_keyword_match():
    """services/correlation's _mitre_mapping only recognizes titles containing
    "failed login" or "powershell" - this is the contract this adapter must
    satisfy for the two services to actually connect meaningfully."""
    alert = build_correlation_alert(SAMPLE_EVENT, SAMPLE_DETECTION)
    assert "failed login" in alert["title"].lower()


def test_build_layer4_output_matches_documented_contract():
    output = build_layer4_output(SAMPLE_EVENT, SAMPLE_DETECTION, entities=["e1"], evidence=["e1"])

    assert set(output.keys()) == {"detection", "severity", "confidence", "entities", "evidence"}
    assert output["detection"]["prediction"] == "malicious"
    assert output["severity"] == "high"
    assert output["confidence"] == 0.85
