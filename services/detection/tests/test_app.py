from unittest.mock import patch

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

SAMPLE_EVENT = {
    "event_id": "evt-123",
    "event_time": "2026-08-23T10:15:02+00:00",
    "source": {"host": "server-01", "log_type": "auth_log", "source_type": "linux"},
    "normalized": {"action": "ssh_login", "outcome": "failure", "user": "admin", "src_ip": "185.220.101.5"},
}

MOCK_MODEL_JSON = '{"prediction": "malicious", "confidence": 0.85, "severity": "high", "mitre": "T1110", "reason": "Brute force pattern."}'


def test_health():
    assert client.get("/health").json() == {"status": "healthy"}


@patch("app.forward_alert")
@patch("app.get_backend")
def test_detect_returns_layer4_output_and_forwards(mock_get_backend, mock_forward):
    mock_get_backend.return_value = lambda prompt: MOCK_MODEL_JSON
    mock_forward.return_value = {"incident_count": 1}

    resp = client.post("/detect", json={"event": SAMPLE_EVENT, "forward": True})

    assert resp.status_code == 200
    body = resp.json()
    assert body["layer4_output"]["detection"]["prediction"] == "malicious"
    assert body["correlation_alert"]["title"] == "Failed login from 185.220.101.5"
    assert body["forward_result"] == {"incident_count": 1}
    mock_forward.assert_called_once()


@patch("app.get_backend")
def test_detect_without_forward_skips_correlation_call(mock_get_backend):
    mock_get_backend.return_value = lambda prompt: MOCK_MODEL_JSON

    resp = client.post("/detect", json={"event": SAMPLE_EVENT, "forward": False})

    assert resp.status_code == 200
    assert resp.json()["forward_result"] is None


@patch("app.get_backend")
def test_detect_returns_503_when_backend_unreachable(mock_get_backend):
    from backends.errors import DetectionBackendError

    def _raise(prompt):
        raise DetectionBackendError("model unreachable")

    mock_get_backend.return_value = _raise

    resp = client.post("/detect", json={"event": SAMPLE_EVENT, "forward": False})
    assert resp.status_code == 503
