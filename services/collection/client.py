"""Forwards normalized events to services/assets's ingest API
(POST /api/v1/ingest/events, the exact contract app/schemas/normalized_event.py
defines)."""
import os
from typing import Any, Dict, List

import requests

ASSETS_URL = os.getenv("ASSETS_URL", "http://localhost:8001")
ASSETS_API_KEY = os.getenv("ASSETS_API_KEY", "change-me-dev-key")


def forward_events(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not events:
        return {"events_processed": 0}

    resp = requests.post(
        f"{ASSETS_URL}/api/v1/ingest/events",
        json=events,
        headers={"X-API-Key": ASSETS_API_KEY},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()
