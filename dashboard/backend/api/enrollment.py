import os
import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from . import auth, database, models, schemas
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    prefix="/api/enrollment",
    tags=["Enrollment"]
)

# IMPORTANT: this must be a reachable address for your target endpoints, not
# 127.0.0.1 (that resolves to the target machine itself, not this server).
# Set SERVER_URL in backend/.env to this machine's LAN IP / hostname, e.g.
# SERVER_URL=http://192.168.1.50:8000
SERVER_URL = os.getenv("SERVER_URL", "http://127.0.0.1:8000")

if SERVER_URL.startswith("http://127.0.0.1") or SERVER_URL.startswith("http://localhost"):
    import logging
    logging.warning(
        "SERVER_URL is set to localhost. Generated agent install commands will "
        "only work if you run them on THIS machine. Set SERVER_URL in backend/.env "
        "to a reachable IP/hostname before enrolling a real remote endpoint."
    )

SUPPORTED_OS_KEYWORDS = ["windows", "ubuntu", "debian", "kali", "centos", "fedora", "linux"]

def validate_os(os_name: str):
    """
    Checked BEFORE the agent row is created. Doing this validation only
    inside generate_commands() (after the DB commit) meant a bad OS value
    still left a permanent orphaned Pending agent behind with a token the
    user never received - confirmed while testing enrollment with an
    unsupported OS. Fail before writing anything.

    macOS is intentionally NOT in this list: install_macos.sh exists and
    handles registration/heartbeat correctly, but real event/log collection
    for macOS isn't implemented (the collector honestly reports "not
    implemented" instead of fabricating events) - it doesn't deliver the
    complete enroll -> real logs -> dashboard pipeline, so it isn't offered
    as a supported OS rather than shipping a partial/misleading option.
    """
    if not any(k in os_name.lower() for k in SUPPORTED_OS_KEYWORDS):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported or not-fully-implemented operating system: {os_name}. "
                   f"Supported: Windows and Linux (Ubuntu/Debian/Kali/CentOS/Fedora)."
        )

def generate_commands(agent_id: int, os_name: str, token: str) -> str:
    base_url = SERVER_URL.rstrip("/")
    os_name = os_name.lower()

    if "windows" in os_name:
        return (
            f'powershell.exe -ExecutionPolicy Bypass -Command '
            f'"$s=Invoke-WebRequest -Uri \'{base_url}/scripts/install.ps1\' -UseBasicParsing; '
            f'Invoke-Expression $s.Content; Install-CySiemAgent -Token \'{token}\' -Server \'{base_url}\' -AgentId {agent_id}"'
        )
    else:
        # validate_os() already guaranteed this matches a Linux keyword or Windows above.
        return f'curl -sSL {base_url}/scripts/install.sh | sudo bash -s -- --token {token} --server {base_url} --agent-id {agent_id}'

@router.post("/enroll", response_model=schemas.AgentResponse)
def enroll_agent(
    agent_in: schemas.AgentCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    validate_os(agent_in.operating_system)

    # secrets.token_urlsafe gives real cryptographic entropy, unlike the old
    # os.urandom(4)-based short token. Only the hash is stored server-side;
    # the raw token is shown to the user exactly once, in the install command.
    raw_token = secrets.token_urlsafe(32)

    new_agent = models.Agent(
        agent_group=agent_in.agent_group,
        operating_system=agent_in.operating_system,
        environment=agent_in.environment,
        status="Pending",
        version="1.0.0",
        enrollment_token=auth.hash_agent_token(raw_token),
        enrollment_token_created_at=datetime.now(timezone.utc)
    )

    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)

    commands = generate_commands(new_agent.id, new_agent.operating_system, raw_token)

    response = schemas.AgentResponse.from_orm(new_agent)
    response.enrollment_commands = commands
    return response

@router.post("/{agent_id}/reissue-token", response_model=schemas.AgentResponse)
def reissue_token(
    agent_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """
    Revokes the agent's current token and issues a new one. Use this for
    re-enrollment/reconnect: the old install on the target machine will
    start getting 401s on its next heartbeat until it's re-installed with
    the new command.
    """
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    raw_token = secrets.token_urlsafe(32)
    agent.enrollment_token = auth.hash_agent_token(raw_token)
    agent.enrollment_token_created_at = datetime.now(timezone.utc)
    agent.status = "Pending"
    db.add(agent)
    db.commit()
    db.refresh(agent)

    commands = generate_commands(agent.id, agent.operating_system, raw_token)
    response = schemas.AgentResponse.from_orm(agent)
    response.enrollment_commands = commands
    return response
