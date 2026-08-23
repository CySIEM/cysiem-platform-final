"""Shared FastAPI dependencies for the v1 API."""
from app.database.session import get_db
from app.security.api_key import verify_api_key

__all__ = ["get_db", "verify_api_key"]
