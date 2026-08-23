"""Shared pytest fixtures. Uses an in-memory SQLite database via
aiosqlite-free async setup by pointing SQLAlchemy at a temporary async
Postgres-compatible URL when available, and falls back gracefully for
pure unit tests that don't touch the database.
"""
import asyncio

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
