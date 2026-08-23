"""AlienVault OTX threat intel connector. Falls back to stub mode if
OTX_API_KEY is not configured.
"""
from __future__ import annotations

from typing import Any, Dict, List

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.core.exceptions import IntegrationError
from app.integrations.base_client import ThreatIntelClient

_OTX_BASE_URL = "https://otx.alienvault.com/api/v1"


class OTXClient(ThreatIntelClient):
    name = "otx"

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.otx_api_key

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    async def lookup_ioc(self, ioc_type: str, value: str) -> Dict[str, Any]:
        if not self.is_configured:
            return {"is_malicious": False, "confidence": 0.0, "source": self.name, "raw": None, "stub": True}
        section_map = {"ip": "IPv4", "domain": "domain", "hash_sha256": "file", "url": "url"}
        section = section_map.get(ioc_type, "IPv4")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{_OTX_BASE_URL}/indicators/{section}/{value}/general",
                    headers={"X-OTX-API-KEY": self._api_key},
                )
                resp.raise_for_status()
                data = resp.json()
                pulse_count = data.get("pulse_info", {}).get("count", 0)
                return {
                    "is_malicious": pulse_count > 0,
                    "confidence": min(0.5 + pulse_count * 0.05, 0.99),
                    "source": self.name,
                    "raw": data,
                    "stub": False,
                }
        except httpx.HTTPError as exc:
            raise IntegrationError(f"OTX lookup failed: {exc}") from exc

    async def fetch_recent_indicators(self, limit: int = 50) -> List[Dict[str, Any]]:
        if not self.is_configured:
            return []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{_OTX_BASE_URL}/pulses/subscribed",
                    headers={"X-OTX-API-KEY": self._api_key},
                    params={"limit": limit},
                )
                resp.raise_for_status()
                return resp.json().get("results", [])
        except httpx.HTTPError as exc:
            raise IntegrationError(f"OTX fetch failed: {exc}") from exc
