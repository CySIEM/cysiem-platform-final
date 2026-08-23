"""Smoke tests for the correlation-service bridge (dashboard/backend has no
pre-existing test suite - this covers the new integration code only)."""
from unittest.mock import Mock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api import models
from api.bridge import (
    _incident_title,
    _severity_bucket,
    ask_copilot,
    get_incident_explanation,
    sync_incidents_from_correlation,
)


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    models.Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_severity_bucket_from_numeric_score():
    assert _severity_bucket(95) == "critical"
    assert _severity_bucket(75) == "high"
    assert _severity_bucket(50) == "medium"
    assert _severity_bucket(10) == "low"


def test_incident_title_prefers_mitre_name():
    incident = {"mitre": [{"technique": "T1110", "name": "Brute Force"}], "summary": "fallback"}
    assert _incident_title(incident) == "Brute Force"


def test_incident_title_falls_back_to_summary():
    incident = {"mitre": [], "summary": "Potential incident on server-01"}
    assert _incident_title(incident) == "Potential incident on server-01"


SAMPLE_INCIDENT = {
    "incident_id": "INC-001",
    "severity_score": 90,
    "status": "open",
    "mitre": [{"technique": "T1110", "name": "Brute Force"}],
}


@patch("api.bridge.requests.get")
def test_sync_incidents_upserts_new_incident(mock_get, db_session):
    mock_get.return_value = Mock(status_code=200, json=lambda: [SAMPLE_INCIDENT])
    mock_get.return_value.raise_for_status = lambda: None

    synced = sync_incidents_from_correlation(db_session)

    assert synced == 1
    row = db_session.query(models.Incident).filter(models.Incident.id == "INC-001").first()
    assert row.title == "Brute Force"
    assert row.severity == "critical"
    assert row.status == "open"


@patch("api.bridge.requests.get")
def test_sync_incidents_updates_existing_row_instead_of_duplicating(mock_get, db_session):
    mock_get.return_value = Mock(status_code=200, json=lambda: [SAMPLE_INCIDENT])
    mock_get.return_value.raise_for_status = lambda: None

    sync_incidents_from_correlation(db_session)
    sync_incidents_from_correlation(db_session)

    assert db_session.query(models.Incident).count() == 1


@patch("api.bridge.requests.get", side_effect=ConnectionError("correlation service down"))
def test_sync_incidents_returns_zero_when_unreachable(mock_get, db_session):
    assert sync_incidents_from_correlation(db_session) == 0


REPORT_RESPONSE = {
    "incident_id": "INC-001",
    "attack_type": "Brute Force",
    "severity": 90,
    "confidence": 85,
    "timeline": [{"id": "alert-101", "timestamp": "2026-08-10T10:00:00Z", "title": "Failed login from PowerShell"}],
    "recommendations": ["Reset impacted credentials"],
}

EXPLAIN_RESPONSE = {
    "incident_id": "INC-001",
    "summary": "This incident reflects a brute-force SSH attack.",
    "severity": 90,
    "risk_score": 85,
    "recommended_actions": ["Reset impacted credentials"],
    "references": ["brute_force.md"],
}


@patch("api.bridge.requests.post")
@patch("api.bridge.requests.get")
def test_get_incident_explanation_combines_report_and_rag_response(mock_get, mock_post):
    mock_get.return_value = Mock(status_code=200, json=lambda: REPORT_RESPONSE)
    mock_get.return_value.raise_for_status = lambda: None
    mock_post.return_value = Mock(status_code=200, json=lambda: EXPLAIN_RESPONSE)
    mock_post.return_value.raise_for_status = lambda: None

    result = get_incident_explanation("INC-001")

    mock_get.assert_called_once_with("http://localhost:8013/report/INC-001", timeout=10)
    mock_post.assert_called_once()
    assert result["summary"] == "This incident reflects a brute-force SSH attack."
    assert result["timeline"] == REPORT_RESPONSE["timeline"]
    assert result["attack_type"] == "Brute Force"


@patch("api.bridge.get_incident_explanation")
def test_ask_copilot_with_incident_id_delegates_to_explanation(mock_explain):
    mock_explain.return_value = EXPLAIN_RESPONSE
    reply = ask_copilot("ignored", incident_id="INC-001")
    assert reply == "This incident reflects a brute-force SSH attack."
    mock_explain.assert_called_once_with("INC-001")


@patch("api.bridge.requests.post")
def test_ask_copilot_without_incident_id_uses_ask_endpoint(mock_post):
    mock_post.return_value = Mock(status_code=200, json=lambda: {"answer": "General answer"})
    mock_post.return_value.raise_for_status = lambda: None

    reply = ask_copilot("What is phishing?")

    assert reply == "General answer"
    mock_post.assert_called_once_with(
        "http://localhost:8014/ask/", json={"question": "What is phishing?"}, timeout=30
    )


def test_response_action_model_records_and_queries(db_session):
    from api.models import ResponseAction

    record = ResponseAction(
        incident_id="INC-001",
        playbook_id="PB-AUTO",
        playbook_title="Simulated response: Reset credentials",
        triggered_by="analyst1",
        status="simulated_complete",
    )
    db_session.add(record)
    db_session.commit()

    rows = db_session.query(ResponseAction).filter(ResponseAction.incident_id == "INC-001").all()
    assert len(rows) == 1
    assert rows[0].status == "simulated_complete"
    assert rows[0].triggered_by == "analyst1"
