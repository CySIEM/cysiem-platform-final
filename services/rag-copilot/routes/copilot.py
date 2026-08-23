from fastapi import APIRouter, HTTPException

from schemas.copilot import (
    CopilotRequest,
    CopilotResponse,
    IncidentExplainRequest,
    IncidentExplainResponse,
)
from services.copilot_service import CopilotUnavailableError, ask, explain_incident

router = APIRouter(tags=["AI Security Copilot"])


@router.post("/ask/", response_model=CopilotResponse)
def ask_copilot(request: CopilotRequest):
    try:
        return ask(request.question)
    except CopilotUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/copilot/explain-incident", response_model=IncidentExplainResponse)
def explain_incident_endpoint(incident: IncidentExplainRequest):
    try:
        return explain_incident(incident.model_dump(exclude_none=True))
    except CopilotUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
