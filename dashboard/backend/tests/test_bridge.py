"""Smoke tests for the correlation-service bridge (dashboard/backend has no
pre-existing test suite - this covers the new integration code only)."""
from unittest.mock import Mock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api import models
from api.bridge import _incident_title, _severity_bucket, sync_incidents_from_correlation


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
