"""Top-level orchestration for a raw log line: entity extraction -> graph
edges -> asset resolution -> IOC / vulnerability enrichment -> risk score.
This is the primary pipeline Team 2 (Layer 3) exposes to the rest of
CySIEM (Layer 2 hands off normalized logs here; Layer 4/5/6 consume the
Asset / IOC / graph output).
"""
from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.events.producer import event_producer
from app.services.asset_discovery_service import AssetDiscoveryService
from app.services.entity_extraction_service import EntityExtractionService
from app.services.graph_service import GraphService
from app.services.ioc_extraction_service import IOCExtractionService
from app.services.vulnerability_enrichment_service import VulnerabilityEnrichmentService


class IngestionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.extraction = EntityExtractionService(session)
        self.assets = AssetDiscoveryService(session)
        self.graph = GraphService(session)
        self.iocs = IOCExtractionService(session)
        self.vulns = VulnerabilityEnrichmentService(session)

    async def ingest_line(self, raw_line: str) -> Dict[str, Any]:
        log_type, entities = await self.extraction.process_line(raw_line)
        entity_dicts: List[Dict[str, Any]] = [
            {"entity_type": e.entity_type.value, "value": e.value, "confidence": e.confidence}
            for e in entities
        ]

        await self.graph.build_edges_from_batch(entity_dicts)
        discovered_assets = await self.assets.discover_from_entities(entity_dicts)
        ioc_verdicts = await self.iocs.evaluate_entities(entity_dicts)
        vuln_records = await self.vulns.enrich_from_entities(entity_dicts)

        await event_producer.publish_entities(entity_dicts)
        malicious = [i for i in ioc_verdicts if i.get("is_malicious")]
        if malicious:
            await event_producer.publish_iocs(malicious)

        return {
            "log_type": log_type,
            "entities_found": len(entity_dicts),
            "entities": entity_dicts,
            "assets_resolved": len(discovered_assets),
            "iocs_evaluated": len(ioc_verdicts),
            "iocs_malicious": len(malicious),
            "vulnerabilities": vuln_records,
        }

    async def ingest_batch(self, lines: List[str]) -> List[Dict[str, Any]]:
        return [await self.ingest_line(line) for line in lines]
