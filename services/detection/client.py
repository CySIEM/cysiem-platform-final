"""Forwards a correlation-shaped alert to services/correlation's POST /ingest."""
import os
from typing import Any, Dict

import requests

CORRELATION_URL = os.getenv("CORRELATION_URL", "http://localhost:8003")


def forward_alert(alert: Dict[str, Any]) -> Dict[str, Any]:
    resp = requests.post(f"{CORRELATION_URL}/ingest", json={"alerts": [alert]}, timeout=30)
    resp.raise_for_status()
    return resp.json()
