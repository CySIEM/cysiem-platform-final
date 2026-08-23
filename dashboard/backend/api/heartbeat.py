from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from . import database, models, auth
from pydantic import BaseModel

router = APIRouter(
    prefix="/api/heartbeat",
    tags=["Heartbeat"]
)

class HeartbeatPayload(BaseModel):
    agent_id: int
    token: str | None = None  # enrollment token issued at /api/enrollment/enroll
    hostname: str | None = None
    ip_address: str | None = None
    os_name: str | None = None
    os_version: str | None = None
    architecture: str | None = None
    mac_address: str | None = None
    current_user: str | None = None
    uptime: str | None = None
    cpu_usage: float | None = 0
    memory_usage: float | None = 0
    disk_usage: float | None = 0
    network_usage: float | None = 0
    version: str | None = "1.0.0"

@router.post("/")
def receive_heartbeat(
    payload: HeartbeatPayload,
    db: Session = Depends(database.get_db)
):
    agent = auth.verify_agent_token(db, payload.agent_id, payload.token)

    # Distinguish "this is the very first contact" (registration) from a
    # recurring heartbeat, so status genuinely moves Pending -> Connecting ->
    # Active instead of jumping straight to Active on one API call.
    is_first_contact = agent.hostname is None

    agent.last_seen = datetime.now(timezone.utc)
    agent.status = "Connecting" if is_first_contact else "Active"

    # Auto-detect/Update fields
    if payload.hostname: agent.hostname = payload.hostname
    if payload.ip_address: agent.ip_address = payload.ip_address
    # NOTE: operating_system is intentionally NOT overwritten here.
    # It's set once at enrollment (Windows/macOS/Ubuntu/Kali/etc - whatever
    # the admin picked, which also determined which install script ran).
    # payload.os_name is only ever the generic platform.system() value
    # ("Linux"), and overwriting with it was replacing a specific,
    # deliberately-chosen label ("Kali") with a less useful generic one on
    # the very first heartbeat - confirmed happening during testing.
    # Kernel-level detail still lands in os_version below.
    if payload.os_version: agent.os_version = payload.os_version
    if payload.architecture: agent.architecture = payload.architecture
    if payload.mac_address: agent.mac_address = payload.mac_address
    if payload.current_user: agent.current_user = payload.current_user
    if payload.uptime: agent.uptime = payload.uptime
    if payload.version: agent.version = payload.version

    # Metrics
    agent.cpu_usage = payload.cpu_usage
    agent.memory_usage = payload.memory_usage
    agent.disk_usage = payload.disk_usage
    agent.network_usage = payload.network_usage

    db.add(agent)
    db.commit()
    return {"status": "success", "timestamp": datetime.now(timezone.utc)}
