from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="SOC Analyst")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    severity = Column(String) # critical, high, medium, low
    name = Column(String)
    src_ip = Column(String)
    dst_ip = Column(String)
    mitre_tactic = Column(String)
    confidence = Column(Integer)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(String, primary_key=True) # e.g. INC-2024-001
    title = Column(String)
    severity = Column(String)
    status = Column(String) # open, investigating, resolved
    assignee = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class ThreatCampaign(Base):
    __tablename__ = "threats"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    severity = Column(String)
    mitre_tag = Column(String)
    description = Column(String)
    confidence = Column(Integer)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())

class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String, nullable=True)
    name = Column(String, nullable=True)
    enrollment_token = Column(String, nullable=True, index=True)  # hashed token; validated on every agent->server call
    enrollment_token_created_at = Column(DateTime(timezone=True), nullable=True)
    operating_system = Column(String, nullable=True)
    os_version = Column(String, nullable=True)
    architecture = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    mac_address = Column(String, nullable=True)
    current_user = Column(String, nullable=True)
    status = Column(String, default="Pending")  # Pending, Connecting, Active, Disconnected, Offline
    version = Column(String, default="1.0.0")
    # No server_default here on purpose: a freshly-enrolled agent has never
    # actually reported in, so last_seen should be NULL ("Never" in the UI)
    # until the first real heartbeat sets it. The old server_default=func.now()
    # made every Pending agent show a fake "X seconds ago" heartbeat time.
    last_seen = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    uptime = Column(String, nullable=True)
    risk_score = Column(Integer, default=0)
    cpu_usage = Column(Float, default=0)
    memory_usage = Column(Float, default=0)
    disk_usage = Column(Float, default=0)
    network_usage = Column(Float, default=0)
    policy = Column(String, default="Default Policy")
    agent_group = Column(String, nullable=True)
    department = Column(String, nullable=True)
    environment = Column(String, nullable=True)
    description = Column(String, nullable=True)
    tags = Column(String, nullable=True)
    owner = Column(String, nullable=True)
    
class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), index=True)
    level = Column(String, index=True)
    source = Column(String)
    event_id = Column(String)
    category = Column(String)
    host = Column(String)
    user = Column(String)
    process = Column(String)
    pid = Column(Integer, nullable=True, index=True)
    command_line = Column(String)
    file_path = Column(String)
    sha256 = Column(String)
    mitre_technique = Column(String)
    ip_address = Column(String)
    message = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)