import os
from typing import List
from . import schemas
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, cast, String
from datetime import datetime, timedelta, timezone
import logging
from . import auth, database, models
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    prefix="/api/agents",
    tags=["Agents"]
)

# Heartbeat interval is 5s by default (config.json on the agent side).
# OFFLINE_TIMEOUT_SECONDS in backend/.env controls how long without a
# heartbeat before an agent flips to Offline - was hardcoded to 5 MINUTES
# before, which made no sense against a 5-second heartbeat and made the
# dashboard look broken/stale during a demo. Default is now 20s (a few
# missed heartbeats' worth of tolerance, not an instant flip on one blip).
OFFLINE_TIMEOUT_SECONDS = float(os.getenv("OFFLINE_TIMEOUT_SECONDS", "20"))


def apply_offline_detection(agents, db: Session):
    """
    Shared by the list endpoint AND the single-agent detail endpoint so
    both agree on status instead of the list page and the detail page
    showing different things for the same agent.
    """
    now = datetime.now(timezone.utc)
    changed = False
    for agent in agents:
        if agent.status in ["Active", "Connecting", "Online"] and agent.last_seen:
            ls = agent.last_seen
            if ls.tzinfo is None:
                ls = ls.replace(tzinfo=timezone.utc)
            if (now - ls).total_seconds() > OFFLINE_TIMEOUT_SECONDS:
                agent.status = "Offline"
                db.add(agent)
                changed = True
    if changed:
        db.commit()

@router.get("/", response_model=List[schemas.AgentDetails])
def get_agents(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    agents = db.query(models.Agent).all()
    apply_offline_detection(agents, db)
    return agents


@router.get("/{agent_id}", response_model=schemas.AgentDetails)
def get_agent_details(
    agent_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    apply_offline_detection([agent], db)
    return agent

@router.put("/{agent_id}", response_model=schemas.AgentResponse)
def update_agent(
    agent_id: int,
    agent_update: schemas.AgentUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    db_agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    update_data = agent_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_agent, key, value)

    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent

@router.delete("/{agent_id}")
def delete_agent(
    agent_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    try:
        db_agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
        if not db_agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Delete associated logs first to satisfy foreign key constraints
        db.query(models.AgentLog).filter(models.AgentLog.agent_id == agent_id).delete(synchronize_session=False)

        # Delete the agent
        db.delete(db_agent)
        db.commit()
        return {"status": "success", "message": f"Agent {agent_id} and associated logs deleted"}
    except Exception as e:
        db.rollback()
        logging.error(f"Error deleting agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete agent: {str(e)}")

@router.get("/{agent_id}/logs")
def get_agent_logs(
    agent_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        # Without this check, a deleted agent's ID still returned a fake
        # "waiting for events" placeholder as if it were a real, live agent
        # that just hadn't reported in yet - confirmed during delete testing.
        raise HTTPException(status_code=404, detail="Agent not found")
    hostname = agent.hostname if agent else "Unknown"
    now = datetime.now(timezone.utc)

    real_logs = db.query(models.AgentLog).filter(
        models.AgentLog.agent_id == agent_id
    ).order_by(models.AgentLog.timestamp.desc()).limit(100).all()

    formatted_logs = []
    for log in real_logs:
        formatted_logs.append({
            "id": log.id,
            "level": log.level,
            "time": log.timestamp.strftime("%H:%M:%S") if log.timestamp else "—",
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "source": log.source,
            "event_id": log.event_id,
            "category": log.category,
            "host": log.host,
            "user": log.user,
            "process": log.process,
            "pid": log.pid,
            "command_line": log.command_line,
            "file_path": log.file_path,
            "sha256": log.sha256,
            "mitre": log.mitre_technique,
            "ip_address": log.ip_address,
            "message": log.message,
            "description": log.message
        })

    if not formatted_logs:
        # Fallback to templates for better demo experience if no real logs yet
        return [
            {
                "id": 9999,
                "level": "INFO",
                "time": now.strftime("%H:%M:%S"),
                "timestamp": now.isoformat(),
                "source": "CySIEM Agent",
                "message": f"Agent initialized on {hostname}. Waiting for event stream...",
                "description": "The agent has successfully connected and is waiting for system events to process."
            }
        ]

    return formatted_logs


# ----------------------------------------------------------------------------
# Historical event search / Kibana-style query API
# ----------------------------------------------------------------------------
# This does NOT replace GET /{agent_id}/logs above (still used wherever a
# simple "last 100" feed is wanted). This is the filtered, paginated,
# time-ranged query the Agent Event Stream's search/time-range/pagination
# controls call - both live polling and "See more events" hit this same
# endpoint, just with different `limit`/filter values, so results are
# always a fresh, consistent, filtered snapshot rather than two separate
# code paths that could disagree.
MAX_EVENTS_LIMIT = 500  # hard ceiling - a SIEM should never dump "everything" in one response

def _format_event(log: models.AgentLog) -> dict:
    return {
        "id": log.id,
        "agent_id": log.agent_id,
        "level": log.level,
        "time": log.timestamp.strftime("%H:%M:%S") if log.timestamp else "—",
        "timestamp": log.timestamp.isoformat() if log.timestamp else None,
        "source": log.source,
        "event_id": log.event_id,
        "category": log.category,
        "host": log.host,
        "user": log.user,
        "process": log.process,
        "pid": log.pid,
        "command_line": log.command_line,
        "file_path": log.file_path,
        "sha256": log.sha256,
        "mitre_technique": log.mitre_technique,
        "ip_address": log.ip_address,
        "message": log.message,
    }

@router.get("/{agent_id}/events")
def get_agent_events(
    agent_id: int,
    search: str | None = Query(None, max_length=200),
    severity: str | None = None,
    source: str | None = None,
    pid: int | None = None,
    process: str | None = Query(None, max_length=200),
    mitre_technique: str | None = Query(None, max_length=100),
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=MAX_EVENTS_LIMIT),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """
    Historical / filtered event query for the Agent Event Stream.
    All filters are applied server-side via SQLAlchemy's parameterized
    query builder (never raw string-concatenated SQL), so user-supplied
    search/filter text cannot be used for SQL injection.
    """
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    query = db.query(models.AgentLog).filter(models.AgentLog.agent_id == agent_id)

    if severity and severity.upper() != "ALL":
        query = query.filter(models.AgentLog.level == severity.upper())

    if source and source.upper() != "ALL":
        query = query.filter(models.AgentLog.source == source)

    if pid is not None:
        query = query.filter(models.AgentLog.pid == pid)

    if process:
        query = query.filter(func.lower(models.AgentLog.process).like(f"%{process.lower()}%"))

    if mitre_technique:
        query = query.filter(func.lower(models.AgentLog.mitre_technique).like(f"%{mitre_technique.lower()}%"))

    # Time range: the query itself filters by timestamp - this is not a
    # frontend slice of an already-loaded list. Naive datetimes (no
    # tzinfo) are treated as UTC, matching how timestamps are stored.
    if start_time:
        st = start_time if start_time.tzinfo else start_time.replace(tzinfo=timezone.utc)
        query = query.filter(models.AgentLog.timestamp >= st)
    if end_time:
        et = end_time if end_time.tzinfo else end_time.replace(tzinfo=timezone.utc)
        query = query.filter(models.AgentLog.timestamp <= et)

    if search:
        term = f"%{search.strip().lower()}%"
        pid_as_text = func.lower(cast(models.AgentLog.pid, String))

        def ci(col):
            return func.lower(func.coalesce(col, ''))

        query = query.filter(or_(
            ci(models.AgentLog.message).like(term),
            ci(models.AgentLog.user).like(term),
            ci(models.AgentLog.process).like(term),
            ci(models.AgentLog.ip_address).like(term),
            ci(models.AgentLog.host).like(term),
            ci(models.AgentLog.source).like(term),
            ci(models.AgentLog.level).like(term),
            ci(models.AgentLog.category).like(term),
            ci(models.AgentLog.mitre_technique).like(term),
            ci(models.AgentLog.event_id).like(term),
            ci(models.AgentLog.command_line).like(term),
            ci(models.AgentLog.file_path).like(term),
            ci(models.AgentLog.sha256).like(term),
            pid_as_text.like(term),
        ))

    total = query.count()
    offset = (page - 1) * limit
    rows = query.order_by(models.AgentLog.timestamp.desc()).offset(offset).limit(limit).all()
    items = [_format_event(r) for r in rows]

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "has_more": (offset + len(items)) < total,
    }
