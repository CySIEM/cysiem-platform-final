"""Periodic threat intel feed sync - pulls recent indicators from MISP/OTX
and upserts them as local IOC records. Invoked by app/workers/threat_intel_sync.py.
"""
from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.misp_client import MISPClient
from app.integrations.otx_client import OTXClient
from app.repositories.ioc_repository import IOCRepository


class ThreatIntelService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = IOCRepository(session)
        self.misp = MISPClient()
        self.otx = OTXClient()

    async def sync_feeds(self, limit: int = 50) -> Dict[str, int]:
        imported = 0
        for client in (self.misp, self.otx):
            if not client.is_configured:
                continue
            indicators: List[Dict[str, Any]] = await client.fetch_recent_indicators(limit=limit)
            for item in indicators:
                value = item.get("value") or item.get("indicator")
                if not value:
                    continue
                existing = await self.repo.find_one(value=value)
                if not existing:
                    await self.repo.create(
                        ioc_type=item.get("type", "unknown"),
                        value=value,
                        source=client.name,
                        confidence=0.7,
                        is_malicious=True,
                    )
                    imported += 1
        return {"imported": imported}
