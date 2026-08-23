"""Thin service wrapper around the singleton GraphEngine, plus persistence
of edges to the database for durability/audit trail.
"""
from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import EdgeType, EntityType
from app.core.graph_engine import graph_engine
from app.models.edge import EntityEdge


class GraphService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def link_entities(
        self,
        src_type: EntityType,
        src_value: str,
        dst_type: EntityType,
        dst_value: str,
        edge_type: EdgeType,
        **attrs: Any,
    ) -> None:
        graph_engine.add_edge(src_type, src_value, dst_type, dst_value, edge_type, **attrs)
        self.session.add(
            EntityEdge(
                src_entity_type=src_type.value,
                src_value=src_value,
                dst_entity_type=dst_type.value,
                dst_value=dst_value,
                edge_type=edge_type.value,
                attributes=attrs,
            )
        )
        await self.session.flush()

    async def build_edges_from_batch(self, entities: List[Dict[str, Any]]) -> int:
        """Heuristic co-occurrence linking: entities extracted from the same
        log line are linked with a best-guess edge type. Real deployments
        should tighten this with source-field-aware parsing per log type.

        Routes every edge through link_entities() so it lands in both the
        in-process graph AND the entity_edges table - previously this
        method wrote only to the in-memory graph, so relationships did not
        survive a process restart. Fixed per review.
        """
        edge_count = 0
        hostnames = [e for e in entities if e["entity_type"] == EntityType.HOSTNAME.value]
        ips = [e for e in entities if e["entity_type"] == EntityType.IP_ADDRESS.value]
        macs = [e for e in entities if e["entity_type"] == EntityType.MAC_ADDRESS.value]
        users = [e for e in entities if e["entity_type"] == EntityType.USERNAME.value]
        domains = [e for e in entities if e["entity_type"] == EntityType.DOMAIN.value]

        for h in hostnames:
            for ip in ips:
                await self.link_entities(
                    EntityType.IP_ADDRESS, ip["value"], EntityType.HOSTNAME, h["value"], EdgeType.IP_TO_HOSTNAME
                )
                edge_count += 1
            for m in macs:
                await self.link_entities(
                    EntityType.IP_ADDRESS, ips[0]["value"] if ips else "unknown", EntityType.MAC_ADDRESS,
                    m["value"], EdgeType.IP_TO_MAC
                )
                edge_count += 1
            for u in users:
                await self.link_entities(EntityType.USERNAME, u["value"], EntityType.HOSTNAME, h["value"], EdgeType.USER_TO_HOST)
                edge_count += 1
        for ip in ips:
            for d in domains:
                await self.link_entities(EntityType.IP_ADDRESS, ip["value"], EntityType.DOMAIN, d["value"], EdgeType.IP_TO_DOMAIN)
                edge_count += 1
        return edge_count

    def stats(self) -> Dict[str, int]:
        return graph_engine.stats()

    def export(self) -> Dict[str, Any]:
        return graph_engine.export_json()
