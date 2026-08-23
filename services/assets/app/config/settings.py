"""Application configuration, loaded from environment variables / .env."""
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    app_name: str = "CySIEM Layer 3 - Asset Intelligence"
    app_env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql+asyncpg://cysiem:cysiem@localhost:5432/cysiem_layer3"
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # Security
    secret_key: str = "change-me-in-production"
    api_key: str = "change-me-dev-key"
    access_token_expire_minutes: int = 60
    jwt_algorithm: str = "HS256"

    # Threat intel integrations
    misp_url: Optional[str] = None
    misp_api_key: Optional[str] = None
    otx_api_key: Optional[str] = None

    # Events
    kafka_bootstrap_servers: Optional[str] = None
    kafka_topic_entities: str = "cysiem.layer3.entities"
    kafka_topic_iocs: str = "cysiem.layer3.iocs"

    # Worker
    threat_intel_sync_interval_minutes: int = 60

    # CORS
    cors_origins: List[str] = ["*"]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
