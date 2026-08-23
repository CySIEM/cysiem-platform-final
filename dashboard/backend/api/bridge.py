"""Bridges the dashboard's own DB-backed views onto the real pipeline.

Team 6's dashboard was built against its own seeded Incident/Alert tables,
entirely decoupled from services/correlation (Team 4) - there was no
integration point at all. Rather than replace Team 6's already-working,
DB-driven /api/dashboard/init response code, this pulls live incidents from
the correlation service and upserts them into Team 6's own `incidents`
table (keyed by the real incident_id), so the existing query/response code
downstream picks them up unchanged.

Alert-table syncing is intentionally left out: Team 4's incidents don't map
onto Team 6's Alert rows without inventing an external-id column that isn't
in the original schema, so bridging that would mean a schema change rather
than pure integration. The Incidents tab reflects the real pipeline; the
Alerts tab keeps showing Team 6's own agent-derived/seeded alerts.
"""
import os
from typing import Any, Dict, List

import requests
from sqlalchemy.orm import Session

from . import models

CORRELATION_URL = os.getenv("CORRELATION_URL", "http://localhost:8003")
RAG_URL = os.getenv("RAG_URL", "http://localhost:8004")


def _severity_bucket(severity_score: Any) -> str:
    try:
        score = float(severity_score)
    except (TypeError, ValueError):
        return str(severity_score or "medium").lower()

    if score >= 90:
        return "critical"
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def _incident_title(incident: Dict[str, Any]) -> str:
    mitre = incident.get("mitre") or []
    if mitre and isinstance(mitre[0], dict) and mitre[0].get("name"):
        return mitre[0]["name"]
    return incident.get("summary") or f"Incident {incident.get('incident_id', '')}"


def sync_incidents_from_correlation(db: Session) -> int:
    """Fetches services/correlation's current incidents and upserts them
    into this service's own Incident table. Returns the number synced, or
    0 (silently) if the correlation service isn't reachable - the dashboard
    should still render with whatever it already has rather than failing.
    """
    try:
        resp = requests.get(f"{CORRELATION_URL}/incidents", timeout=5)
        resp.raise_for_status()
        incidents: List[Dict[str, Any]] = resp.json()
    except Exception:
        return 0

    synced = 0
    for incident in incidents:
        incident_id = incident.get("incident_id")
        if not incident_id:
            continue

        row = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
        if row is None:
            row = models.Incident(id=incident_id)
            db.add(row)

        row.title = _incident_title(incident)
        row.severity = _severity_bucket(incident.get("severity_score"))
        row.status = incident.get("status") or "open"
        synced += 1

    db.commit()
    return synced


def ask_copilot(query: str, incident_id: str | None = None) -> str:
    """Proxies a copilot question to the real rag-copilot service. Callers
    should catch exceptions and fall back to a canned response so the chat
    UI doesn't hard-fail when that service is down."""
    if incident_id:
        resp = requests.get(f"{CORRELATION_URL}/report/{incident_id}", timeout=10)
        resp.raise_for_status()
        incident = resp.json()
        resp = requests.post(f"{RAG_URL}/copilot/explain-incident", json=incident, timeout=30)
        resp.raise_for_status()
        return resp.json()["summary"]

    resp = requests.post(f"{RAG_URL}/ask/", json={"question": query}, timeout=30)
    resp.raise_for_status()
    return resp.json()["answer"]
