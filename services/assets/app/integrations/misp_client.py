"""MISP threat intel connector. Falls back to stub mode if MISP_URL /
MISP_API_KEY are not configured, so Layer 3 remains runnable offline.
"""
from __future__ import annotations

from typing import Any, Dict, List

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.core.exceptions import IntegrationError
from app.integrations.base_client import ThreatIntelClient


class MISPClient(ThreatIntelClient):
    name = "misp"

    def __init__(self) -> None:
        settings = get_settings()
        self._url = settings.misp_url
        self._api_key = settings.misp_api_key

    @property
    def is_configured(self) -> bool:
        return bool(self._url and self._api_key)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    async def lookup_ioc(self, ioc_type: str, value: str) -> Dict[str, Any]:
        if not self.is_configured:
            return {"is_malicious": False, "confidence": 0.0, "source": self.name, "raw": None, "stub": True}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self._url}/attributes/restSearch",
                    headers={"Authorization": self._api_key, "Accept": "application/json"},
                    json={"value": value, "type": ioc_type},
                )
                resp.raise_for_status()
                data = resp.json()
                matches = data.get("response", {}).get("Attribute", [])
                return {
                    "is_malicious": len(matches) > 0,
                    "confidence": 0.9 if matches else 0.0,
                    "source": self.name,
                    "raw": matches,
                    "stub": False,
                }
        except httpx.HTTPError as exc:
            raise IntegrationError(f"MISP lookup failed: {exc}") from exc

    async def fetch_recent_indicators(self, limit: int = 50) -> List[Dict[str, Any]]:
        if not self.is_configured:
            return []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self._url}/attributes/restSearch",
                    headers={"Authorization": self._api_key, "Accept": "application/json"},
                    json={"limit": limit},
                )
                resp.raise_for_status()
                return resp.json().get("response", {}).get("Attribute", [])
        except httpx.HTTPError as exc:
            raise IntegrationError(f"MISP fetch failed: {exc}") from exc
