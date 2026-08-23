from unittest.mock import patch

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def _fake_ollama_chat(**kwargs):
    return {"message": {"content": "Mocked security analysis response."}}


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy"}


@patch("services.copilot_service.ollama.chat", side_effect=_fake_ollama_chat)
def test_ask_endpoint_returns_grounded_answer(mock_chat):
    resp = client.post("/ask/", json={"question": "What is a brute force attack?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["answer"] == "Mocked security analysis response."
    assert len(body["sources"]) > 0
    mock_chat.assert_called_once()


@patch("services.copilot_service.ollama.chat", side_effect=_fake_ollama_chat)
def test_explain_incident_endpoint(mock_chat):
    incident = {
        "incident_id": "INC-001",
        "attack_type": "Brute Force",
        "severity": 90,
        "confidence": 85,
        "mitre": [{"technique": "T1110", "name": "Brute Force"}],
        "recommendations": ["Reset impacted credentials"],
    }
    resp = client.post("/copilot/explain-incident", json=incident)
    assert resp.status_code == 200
    body = resp.json()
    assert body["incident_id"] == "INC-001"
    assert body["summary"] == "Mocked security analysis response."
    assert body["recommended_actions"] == ["Reset impacted credentials"]


def test_ask_endpoint_returns_503_when_ollama_unreachable():
    with patch("services.copilot_service.ollama.chat", side_effect=ConnectionError("no ollama")):
        resp = client.post("/ask/", json={"question": "What is phishing?"})
    assert resp.status_code == 503
