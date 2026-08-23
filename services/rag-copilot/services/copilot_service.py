"""AI Security Copilot: retrieval-augmented question answering and
incident explanation, backed by the FAISS knowledge base built in
ai-services/embeddings (see rag/retriever.py) and an Ollama chat model.

This replaces Team 5's original Team5Service, which was a hardcoded
keyword-matcher stub never actually wired to the RAG pipeline the team
had already built in ai-services/copilot/app.py. That real pipeline is
what's implemented here, made reachable through the main FastAPI app
instead of living as a disconnected standalone script.
"""
import os

import ollama

from rag.retriever import search

COPILOT_MODEL = os.getenv("COPILOT_MODEL", "llama3.2")

SYSTEM_PROMPT = """You are an AI Security Copilot for a SIEM platform.
Answer using the provided cybersecurity context when it's relevant.
If the context doesn't cover the question, say so plainly, then answer
from general security knowledge. Keep answers concise and analyst-facing."""

INCIDENT_SYSTEM_PROMPT = """You are an AI Security Copilot explaining a
correlated security incident to a SOC analyst. Use the provided
cybersecurity reference context plus the incident's own evidence.
Respond with a short plain-language summary of what happened, why it's
risky, and 2-4 concrete recommended actions. Be specific to the incident,
not generic advice."""


class CopilotUnavailableError(RuntimeError):
    """Raised when the Ollama backend can't be reached."""


def _chat(system_prompt: str, user_prompt: str) -> str:
    try:
        response = ollama.chat(
            model=COPILOT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response["message"]["content"]
    except Exception as exc:  # ollama.ResponseError, ConnectionError, etc.
        raise CopilotUnavailableError(
            f"Could not reach Ollama model '{COPILOT_MODEL}': {exc}"
        ) from exc


def ask(question: str) -> dict:
    docs = search(question, k=3)
    context = "\n\n".join(doc["content"] for doc in docs)
    sources = [doc["filename"] for doc in docs]

    prompt = f"Context:\n{context}\n\nQuestion:\n{question}"
    answer = _chat(SYSTEM_PROMPT, prompt)

    return {"success": True, "question": question, "answer": answer, "sources": sources}


def _incident_query_text(incident: dict) -> str:
    """Build a retrieval query out of whatever the incident actually contains."""
    parts = []
    attack_type = incident.get("attack_type") or incident.get("summary")
    if attack_type:
        parts.append(str(attack_type))
    mitre = incident.get("mitre") or []
    for m in mitre:
        if isinstance(m, dict):
            parts.append(m.get("name") or m.get("technique") or "")
        else:
            parts.append(str(m))
    root_cause = incident.get("root_cause")
    if isinstance(root_cause, dict) and root_cause.get("root_cause"):
        parts.append(root_cause["root_cause"])
    return " ".join(p for p in parts if p) or "security incident"


def explain_incident(incident: dict) -> dict:
    """incident: the shape returned by the correlation service's
    GET /report/{incident_id} (incident_id, affected_host, attack_type,
    timeline, root_cause, severity, confidence, recommendations) - or the
    richer /incidents record. Extra fields are ignored, missing ones are
    tolerated, so either shape works.
    """
    query = _incident_query_text(incident)
    docs = search(query, k=3)
    context = "\n\n".join(doc["content"] for doc in docs)
    sources = [doc["filename"] for doc in docs]

    prompt = (
        f"Reference context:\n{context}\n\n"
        f"Incident data:\n{incident}\n\n"
        "Summarize the incident, its risk, and recommended next actions."
    )
    narrative = _chat(INCIDENT_SYSTEM_PROMPT, prompt)

    severity = incident.get("severity") or incident.get("severity_score") or "unknown"
    risk_score = incident.get("confidence") or incident.get("confidence_score") or 0
    recommended_actions = incident.get("recommendations") or []
    if isinstance(recommended_actions, str):
        recommended_actions = [recommended_actions]

    return {
        "incident_id": incident.get("incident_id"),
        "summary": narrative,
        "severity": severity,
        "risk_score": risk_score,
        "recommended_actions": recommended_actions,
        "references": sources,
    }
