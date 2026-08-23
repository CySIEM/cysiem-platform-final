from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from . import database, models, auth
from pydantic import BaseModel
from typing import List

router = APIRouter(
    prefix="/api/logs",
    tags=["Logs"]
)

# ----------------------------------------------------------------------------
# CRITICAL severity: real correlation rule, not a per-line fabrication.
# A single failed login is HIGH (see collector.py). Several failed logins
# from the SAME source IP against the SAME agent within a short window is a
# distinct, higher-confidence signal - a brute-force attempt - and gets its
# own CRITICAL correlation event. This only runs server-side because
# correlation across multiple events requires the stored history, which the
# agent-side collector doesn't have visibility into.
# ----------------------------------------------------------------------------
BRUTEFORCE_THRESHOLD = 5          # failed logins...
BRUTEFORCE_WINDOW_SECONDS = 120   # ...within this many seconds...
BRUTEFORCE_COOLDOWN_SECONDS = 300  # ...triggers at most one CRITICAL alert per IP per this cooldown

def _check_bruteforce_correlation(db: Session, agent, ip_address: str):
    if not ip_address:
        return
    now = datetime.now(timezone.utc)

    recent_failures = db.query(models.AgentLog).filter(
        models.AgentLog.agent_id == agent.id,
        models.AgentLog.category == "Authentication",
        models.AgentLog.level == "HIGH",
        models.AgentLog.ip_address == ip_address,
        models.AgentLog.timestamp >= now - timedelta(seconds=BRUTEFORCE_WINDOW_SECONDS),
    ).count()

    if recent_failures < BRUTEFORCE_THRESHOLD:
        return

    already_alerted = db.query(models.AgentLog).filter(
        models.AgentLog.agent_id == agent.id,
        models.AgentLog.category == "Correlation",
        models.AgentLog.ip_address == ip_address,
        models.AgentLog.timestamp >= now - timedelta(seconds=BRUTEFORCE_COOLDOWN_SECONDS),
    ).first()
    if already_alerted:
        return

    db.add(models.AgentLog(
        agent_id=agent.id,
        level="CRITICAL",
        source="Correlation Engine",
        category="Correlation",
        host=agent.hostname,
        ip_address=ip_address,
        mitre_technique="T1110",
        message=f"Possible brute-force attack: {recent_failures} failed logins from {ip_address} "
                f"within {BRUTEFORCE_WINDOW_SECONDS} seconds",
        timestamp=now,
    ))

class LogEntry(BaseModel):
    level: str = "INFO"
    source: str = "System"
    event_id: str | None = None
    category: str | None = None
    user: str | None = None
    process: str | None = None
    pid: int | None = None
    command_line: str | None = None
    file_path: str | None = None
    sha256: str | None = None
    mitre_technique: str | None = None
    ip_address: str | None = None  # e.g. an SSH client source IP - distinct from the agent's own management IP
    message: str
    timestamp: datetime | None = None

class LogPayload(BaseModel):
    agent_id: int
    token: str | None = None  # enrollment token issued at /api/enrollment/enroll
    logs: List[LogEntry]

@router.get("/recent")
def get_recent_logs(
    limit: int = 50,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """
    Real cross-agent log feed for the dashboard's Event Logs view.
    This replaces a client-side random log generator that used to fabricate
    entries like "Signature match: Cobalt Strike Beacon" every second -
    those never came from any agent or detection engine.
    Returns an empty list if no agent has sent logs yet; the frontend should
    show that honestly instead of inventing activity to fill the screen.
    """
    limit = max(1, min(limit, 200))
    rows = (
        db.query(models.AgentLog)
        .order_by(models.AgentLog.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": log.id,
            "agent_id": log.agent_id,
            "level": log.level,
            "time": log.timestamp.strftime("%H:%M:%S") if log.timestamp else "—",
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "source": log.source,
            "host": log.host,
            "message": log.message,
        }
        for log in rows
    ]

@router.post("/ingest")
def ingest_logs(
    payload: LogPayload,
    db: Session = Depends(database.get_db)
):
    agent = auth.verify_agent_token(db, payload.agent_id, payload.token)

    failure_ips_to_check = set()

    for entry in payload.logs:
        new_log = models.AgentLog(
            agent_id=payload.agent_id,
            level=entry.level,
            source=entry.source,
            event_id=entry.event_id,
            category=entry.category,
            host=agent.hostname,
            user=entry.user,
            process=entry.process,
            pid=entry.pid,
            command_line=entry.command_line,
            file_path=entry.file_path,
            sha256=entry.sha256,
            mitre_technique=entry.mitre_technique,
            # Prefer the event's own IP (e.g. an SSH client source address
            # the collector parsed out of the log line) over the agent's own
            # management IP - these are frequently different, and collapsing
            # them to always be the agent's IP was losing real forensic data
            # (and breaking "search by source IP" for auth events).
            ip_address=entry.ip_address or agent.ip_address,
            message=entry.message,
            timestamp=entry.timestamp or datetime.now(timezone.utc)
        )
        db.add(new_log)

        if entry.level == "HIGH" and entry.category == "Authentication" and entry.ip_address:
            failure_ips_to_check.add(entry.ip_address)

    db.commit()

    if failure_ips_to_check:
        for ip in failure_ips_to_check:
            _check_bruteforce_correlation(db, agent, ip)
        db.commit()

    return {"status": "success", "count": len(payload.logs)}
