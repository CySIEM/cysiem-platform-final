"""Extracts candidate IOCs from entities and checks them against configured
threat intel feeds (MISP, OTX). Runs in stub mode automatically when no
feed credentials are configured.
"""
from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import EntityType, IOCType
from app.integrations.misp_client import MISPClient
from app.integrations.otx_client import OTXClient
from app.repositories.ioc_repository import IOCRepository

_ENTITY_TO_IOC_TYPE = {
    EntityType.IP_ADDRESS.value: IOCType.IP.value,
    EntityType.DOMAIN.value: IOCType.DOMAIN.value,
    EntityType.URL.value: IOCType.URL.value,
    EntityType.FILE_HASH.value: IOCType.HASH_SHA256.value,
    EntityType.EMAIL.value: IOCType.EMAIL.value,
}


class IOCExtractionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = IOCRepository(session)
        self.misp = MISPClient()
        self.otx = OTXClient()

    async def evaluate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for entity in entities:
            ioc_type = _ENTITY_TO_IOC_TYPE.get(entity.get("entity_type"))
            if not ioc_type:
                continue
            verdict = await self._check_feeds(ioc_type, entity["value"])
            existing = await self.repo.find_one(value=entity["value"])
            if existing:
                await self.repo.update(
                    existing.id,
                    is_malicious=existing.is_malicious or verdict["is_malicious"],
                    confidence=max(existing.confidence, verdict["confidence"]),
                )
            else:
                await self.repo.create(
                    ioc_type=ioc_type,
                    value=entity["value"],
                    source=verdict["source"],
                    confidence=verdict["confidence"],
                    is_malicious=verdict["is_malicious"],
                )
            results.append({"value": entity["value"], "ioc_type": ioc_type, **verdict})
        return results

    async def _check_feeds(self, ioc_type: str, value: str) -> Dict[str, Any]:
        misp_result = await self.misp.lookup_ioc(ioc_type, value)
        if misp_result["is_malicious"]:
            return misp_result
        otx_result = await self.otx.lookup_ioc(ioc_type, value)
        if otx_result["is_malicious"]:
            return otx_result
        return misp_result if misp_result["source"] else otx_result
