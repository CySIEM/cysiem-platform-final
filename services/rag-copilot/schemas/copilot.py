from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class CopilotRequest(BaseModel):
    question: str


class CopilotResponse(BaseModel):
    success: bool
    question: str
    answer: str
    sources: List[str] = []

    class Config:
        from_attributes = True


class IncidentExplainRequest(BaseModel):
    """Accepts whatever shape the correlation service's incident/report
    endpoints already produce - extra fields are allowed since Team 4's
    incident dict has more fields than any one downstream consumer needs."""

    model_config = ConfigDict(extra="allow")

    incident_id: Optional[str] = None
    attack_type: Optional[str] = None
    severity: Optional[Any] = None
    confidence: Optional[Any] = None
    timeline: Optional[List[Dict[str, Any]]] = None
    mitre: Optional[List[Any]] = None
    root_cause: Optional[Any] = None
    recommendations: Optional[List[str]] = None
    evidence: Optional[Any] = None


class IncidentExplainResponse(BaseModel):
    incident_id: Optional[str] = None
    summary: str
    severity: Optional[Any] = None
    risk_score: Optional[Any] = None
    recommended_actions: List[str] = []
    references: List[str] = []