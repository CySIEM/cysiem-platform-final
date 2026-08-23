from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from api.incident_api import analyze_incidents
from api.persistence import list_incidents, upsert_incident

app = FastAPI(title="Team 4 Correlation API")


class AlertPayload(BaseModel):
    alerts: List[Dict[str, Any]]


class StatusUpdate(BaseModel):
    status: str


@app.post("/ingest")
def ingest_alerts(payload: AlertPayload) -> Dict[str, Any]:
    result = analyze_incidents(payload.alerts)
    for incident in result.get("incidents", []):
        upsert_incident(incident)
    return result


@app.get("/incidents")
def get_incidents() -> List[Dict[str, Any]]:
    return list_incidents()


@app.put("/incidents/{incident_id}")
def update_incident_status(incident_id: str, payload: StatusUpdate) -> Dict[str, Any]:
    incidents = list_incidents()
    for incident in incidents:
        if incident.get("incident_id") == incident_id:
            incident["status"] = payload.status
            upsert_incident(incident)
            return incident
    raise HTTPException(status_code=404, detail="Incident not found")


@app.get("/timeline/{incident_id}")
def get_timeline(incident_id: str) -> List[Dict[str, Any]]:
    incidents = list_incidents()
    for incident in incidents:
        if incident.get("incident_id") == incident_id:
            return incident.get("timeline", incident.get("alerts", []))
    raise HTTPException(status_code=404, detail="Incident not found")


@app.get("/evidence/{incident_id}")
def get_evidence(incident_id: str) -> Dict[str, Any]:
    incidents = list_incidents()
    for incident in incidents:
        if incident.get("incident_id") == incident_id:
            return incident.get("evidence", {})
    raise HTTPException(status_code=404, detail="Incident not found")


@app.get("/report/{incident_id}")
def get_report(incident_id: str) -> Dict[str, Any]:
    incidents = list_incidents()
    for incident in incidents:
        if incident.get("incident_id") == incident_id:
            return {
                "incident_id": incident.get("incident_id"),
                "affected_host": incident.get("target"),
                "attack_type": incident.get("mitre", [{}])[0].get("name"),
                "timeline": incident.get("alerts", []),
                "root_cause": incident.get("root_cause", {}).get("root_cause"),
                "severity": incident.get("severity_score"),
                "confidence": incident.get("confidence_score"),
                "recommendations": incident.get("root_cause", {}).get("recommendations", []),
            }
    raise HTTPException(status_code=404, detail="Incident not found")


@app.get("/root-cause/{incident_id}")
def get_root_cause(incident_id: str) -> Dict[str, Any]:
    incidents = list_incidents()
    for incident in incidents:
        if incident.get("incident_id") == incident_id:
            return incident.get("root_cause", {})
    raise HTTPException(status_code=404, detail="Incident not found")
