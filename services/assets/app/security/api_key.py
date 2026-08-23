"""Simple API-key auth dependency for service-to-service calls between
Layer 3 and the other CySIEM layers/teams.
"""
from fastapi import Depends, Header

from app.config import get_settings
from app.core.exceptions import AuthenticationError


async def verify_api_key(x_api_key: str = Header(default="")) -> str:
    settings = get_settings()
    if x_api_key != settings.api_key:
        raise AuthenticationError("Invalid or missing API key")
    return x_api_key
