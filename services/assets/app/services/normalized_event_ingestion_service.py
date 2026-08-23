"""Ingestion path for Team 1's structured NormalizedEvent JSON (as opposed
to app/services/ingestion_service.py, which handles raw unstructured log
text). This is the path real production traffic from Layer 2 is expected
to use - it trusts Team 1's already-parsed fields instead of re-deriving
everything with regex, and only falls back to regex for what Team 1
doesn't structure yet (MAC addresses, embedded hashes/CVEs/domains).
"""
from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import EdgeType, EntityType
from app.core.normalized_event_mapper import build_asset_context, extract_entities, is_failed_event
from app.events.producer import event_producer
from app.schemas.normalized_event import NormalizedEvent, NormalizedIngestResult
from app.services.asset_discovery_service import AssetDiscoveryService
from app.services.entity_extraction_service import EntityExtractionService
from app.services.graph_service import GraphService
from app.services.ioc_extraction_service import IOCExtractionService
from app.services.vulnerability_enrichment_service import VulnerabilityEnrichmentService


class NormalizedEventIngestionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.extraction = EntityExtractionService(session)
        self.assets = AssetDiscoveryService(session)
        self.graph = GraphService(session)
        self.iocs = IOCExtractionService(session)
        self.vulns = VulnerabilityEnrichmentService(session)

    async def ingest_event(self, event: NormalizedEvent) -> Dict[str, Any]:
        entities = extract_entities(event)
        await self.extraction.persist_entities(entities, source_log_type=event.source.log_type)

        entity_dicts: List[Dict[str, Any]] = [
            {"entity_type": e.entity_type.value, "value": e.value, "confidence": e.confidence} for e in entities
        ]

        edge_count = await self._link_event_entities(event)

        asset = None
        if event.source.host:
            context = build_asset_context(event)
            asset = await self.assets.upsert_asset_from_context(
                event.source.host, context, increment_failed_auth=is_failed_event(event)
            )

        ioc_verdicts = await self.iocs.evaluate_entities(entity_dicts)
        vuln_records = await self.vulns.enrich_from_entities(
            entity_dicts, asset_id=str(asset.id) if asset else None
        )

        await event_producer.publish_entities(entity_dicts)
        malicious = [i for i in ioc_verdicts if i.get("is_malicious")]
        if malicious:
            await event_producer.publish_iocs(malicious)

        return {
            "event_id": event.event_id,
            "log_type": event.source.log_type,
            "action": event.normalized.action,
            "entities_found": len(entity_dicts),
            "edges_created": edge_count,
            "asset_id": str(asset.id) if asset else None,
            "iocs_evaluated": len(ioc_verdicts),
            "iocs_malicious": len(malicious),
            "vulnerabilities": vuln_records,
            "failed_event": is_failed_event(event),
        }

    async def ingest_batch(self, events: List[NormalizedEvent]) -> NormalizedIngestResult:
        errors: List[str] = []
        totals = dict(
            entities_found=0, assets_resolved=0, iocs_evaluated=0,
            iocs_malicious=0, vulnerabilities=0, failed_auth_events=0,
        )
        resolved_assets = set()

        for event in events:
            try:
                result = await self.ingest_event(event)
            except Exception as exc:  # noqa: BLE001 - one bad event must not sink the batch
                errors.append(f"{event.event_id or 'unknown'}: {exc}")
                continue
            totals["entities_found"] += result["entities_found"]
            totals["iocs_evaluated"] += result["iocs_evaluated"]
            totals["iocs_malicious"] += result["iocs_malicious"]
            totals["vulnerabilities"] += len(result["vulnerabilities"])
            if result.get("failed_event"):
                totals["failed_auth_events"] += 1
            if result.get("asset_id"):
                resolved_assets.add(result["asset_id"])

        return NormalizedIngestResult(
            events_processed=len(events),
            entities_found=totals["entities_found"],
            assets_resolved=len(resolved_assets),
            iocs_evaluated=totals["iocs_evaluated"],
            iocs_malicious=totals["iocs_malicious"],
            vulnerabilities=totals["vulnerabilities"],
            failed_auth_events=totals["failed_auth_events"],
            errors=errors,
        )

    async def _link_event_entities(self, event: NormalizedEvent) -> int:
        """Build graph edges directly from Team 1's structured fields -
        higher-confidence than the heuristic co-occurrence linking the
        raw-line pipeline has to fall back to, since we already know
        exactly which field each value came from.
        """
        src = event.source
        norm = event.normalized
        count = 0

        if src.host and src.ip:
            await self.graph.link_entities(
                EntityType.IP_ADDRESS, src.ip, EntityType.HOSTNAME, src.host, EdgeType.IP_TO_HOSTNAME
            )
            count += 1

        context_macs = build_asset_context(event)["mac_addresses"]
        for mac in context_macs:
            anchor_ip = src.ip or (norm.src_ip if norm.src_ip else None)
            if anchor_ip:
                await self.graph.link_entities(
                    EntityType.IP_ADDRESS, anchor_ip, EntityType.MAC_ADDRESS, mac, EdgeType.IP_TO_MAC
                )
                count += 1

        if norm.user and not norm.user.isdigit() and src.host:
            await self.graph.link_entities(
                EntityType.USERNAME, norm.user, EntityType.HOSTNAME, src.host, EdgeType.USER_TO_HOST
            )
            count += 1

        if norm.process_name and src.host:
            await self.graph.link_entities(
                EntityType.HOSTNAME, src.host, EntityType.PROCESS, norm.process_name, EdgeType.HOST_TO_PROCESS
            )
            count += 1

        if norm.src_ip and norm.dest_ip:
            await self.graph.link_entities(
                EntityType.IP_ADDRESS, norm.src_ip, EntityType.IP_ADDRESS, norm.dest_ip, EdgeType.COMMUNICATES_WITH
            )
            count += 1

        return count
