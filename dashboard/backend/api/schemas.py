# from pydantic import BaseModel

# class UserBase(BaseModel):
#     username: str

# class UserCreate(UserBase):
#     password: str

# class UserResponse(UserBase):
#     id: int
#     role: str
#     class Config:
#         from_attributes = True

# class Token(BaseModel):
#     access_token: str
#     token_type: str

from pydantic import BaseModel, Field, field_validator
import re
from datetime import datetime

class UserBase(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        description="Username must be between 3 and 30 characters."
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, value):
        value = value.strip()

        if not value:
            raise ValueError("Username cannot be empty.")

        # Only allow letters, numbers, underscore and dot
        if not re.fullmatch(r"^[A-Za-z0-9._]+$", value):
            raise ValueError(
                "Username can contain only letters, numbers, '.' and '_'."
            )

        return value


class UserCreate(UserBase):
    password: str = Field(
        ...,
        min_length=8,
        max_length=64,
        description="Password must be between 8 and 64 characters."
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):

        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters.")

        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain one uppercase letter.")

        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain one lowercase letter.")

        if not re.search(r"\d", value):
            raise ValueError("Password must contain one number.")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=/\\[\]]", value):
            raise ValueError("Password must contain one special character.")

        return value


class UserResponse(UserBase):
    id: int
    role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str

#Agent class
class AgentCreate(BaseModel):
    agent_group: str
    operating_system: str
    environment: str | None = "Production"

class AgentUpdate(BaseModel):
    agent_group: str | None = None
    environment: str | None = None
    department: str | None = None
    description: str | None = None
    tags: str | None = None
    owner: str | None = None

class AgentResponse(BaseModel):
    id: int
    hostname: str | None = None
    name: str | None = None
    operating_system: str | None = None
    ip_address: str | None = None
    agent_group: str | None = None
    environment: str | None = None
    status: str
    version: str
    enrollment_commands: str | None = None

    class Config:
        from_attributes = True

class AgentDetails(AgentResponse):
    created_at: datetime | None = None
    last_seen: datetime | None = None  # None means the agent has never actually connected ("Never" in the UI)
    os_version: str | None = None
    architecture: str | None = None
    mac_address: str | None = None
    current_user: str | None = None
    uptime: str | None = None
    risk_score: int
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_usage: float
    policy: str
    agent_group: str | None = None
    department: str | None = None
    environment: str | None = None
    description: str | None = None
    tags: str | None = None
    owner: str | None = None

    class Config:
        from_attributes = True

class AgentLogResponse(BaseModel):
    id: int
    level: str
    source: str
    event_id: str | None = None
    category: str | None = None
    host: str | None = None
    user: str | None = None
    process: str | None = None
    command_line: str | None = None
    file_path: str | None = None
    sha256: str | None = None
    mitre_technique: str | None = None
    ip_address: str | None = None
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True