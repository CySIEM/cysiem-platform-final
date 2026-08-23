# import os
# from datetime import datetime, timedelta
# from typing import Optional
# from jose import JWTError, jwt
# import bcrypt
import os
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from . import database, models

# In a real app, load this from env
# SECRET_KEY = "cysiem_super_secret_key_beta_model_only"
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day

# Load environment variables
load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY not found. Create backend/.env and add JWT_SECRET_KEY."
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

import hashlib
from fastapi import HTTPException

def hash_agent_token(raw_token: str) -> str:
    """
    Agent tokens are generated per-enrollment and sent by the agent on every
    call. We store a SHA-256 hash (not bcrypt: this runs on every heartbeat/
    log ingest call, so it needs to be fast, and the token already has high
    entropy from secrets.token_urlsafe, so a fast hash is fine here).
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

import os
from datetime import datetime, timezone

ENROLLMENT_TOKEN_TTL_HOURS = float(os.getenv("ENROLLMENT_TOKEN_TTL_HOURS", "24"))

def verify_agent_token(db: Session, agent_id: int, raw_token: str | None):
    """
    Looks up the agent and checks the provided token against the stored hash.
    Raises 401/403/404 with a specific reason instead of failing silently,
    so install scripts and the dashboard can show a real error instead of
    a generic 'connection refused'.
    Returns the agent row on success.

    Expiry only applies before an agent has EVER successfully registered
    (agent.hostname is still None) - an enrollment command sitting unused
    for too long should stop working. Once an agent has registered at least
    once, this same token is its permanent operating credential for
    heartbeats/logs; expiring it after a fixed TTL would kill every
    long-running agent on a timer, which contradicts "the agent must keep
    running / reconnect after reboot". Revocation for an already-running
    agent still works via delete or /enrollment/{id}/reissue-token.
    """
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found. It may have been deleted from the platform.")
    if not agent.enrollment_token:
        # Agent enrolled before token validation existed, or token was never set.
        raise HTTPException(status_code=403, detail="Agent has no enrollment token on record. Re-enroll this agent.")
    if not raw_token:
        raise HTTPException(status_code=401, detail="Missing enrollment token.")

    if not agent.hostname and agent.enrollment_token_created_at:
        created = agent.enrollment_token_created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        age_hours = (datetime.now(timezone.utc) - created).total_seconds() / 3600
        if age_hours > ENROLLMENT_TOKEN_TTL_HOURS:
            raise HTTPException(
                status_code=401,
                detail=f"Enrollment token expired ({ENROLLMENT_TOKEN_TTL_HOURS}h limit, never completed registration). "
                       f"Generate a new install command from the dashboard."
            )

    if hash_agent_token(raw_token) != agent.enrollment_token:
        raise HTTPException(status_code=401, detail="Invalid or revoked enrollment token.")
    return agent

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
