"""Entity resolution: merges raw entities (IPs, hostnames, MACs, usernames)
that co-occur in the graph into logical Asset records, so the same
physical host isn't tracked as N disconnected indicators.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import EntityType
from app.core.graph_engine import graph_engine
from app.models.asset import Asset
from app.repositories.asset_repository import AssetRepository


class AssetDiscoveryService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = AssetRepository(session)

    async def resolve_asset_for_hostname(self, hostname: str) -> Optional[Asset]:
        """Walk the graph outward from a hostname to gather its known IPs,
        MACs, and usernames, then upsert a single Asset record."""
        neighbors = graph_engine.neighbors(EntityType.HOSTNAME, hostname)
        ip_addresses: List[str] = []
        mac_addresses: List[str] = []
        usernames: List[str] = []

        for n in neighbors:
            node = n["node"]
            if node.get("entity_type") == EntityType.IP_ADDRESS.value:
                ip_addresses.append(node["value"])
            elif node.get("entity_type") == EntityType.MAC_ADDRESS.value:
                mac_addresses.append(node["value"])
            elif node.get("entity_type") == EntityType.USERNAME.value:
                usernames.append(node["value"])

        existing = await self.repo.find_one(primary_identifier=hostname, asset_type="host")
        payload: Dict[str, Any] = dict(
            asset_type="host",
            primary_identifier=hostname,
            hostname=hostname,
            ip_addresses=sorted(set(ip_addresses)),
            mac_addresses=sorted(set(mac_addresses)),
            usernames=sorted(set(usernames)),
        )
        if existing:
            return await self.repo.update(existing.id, **payload)
        return await self.repo.create(**payload)

    async def resolve_asset_for_ip(self, ip: str) -> Optional[Asset]:
        """Upsert a device-type asset anchored on a bare IP address, for
        log lines that carry no hostname (e.g. raw firewall/IDS traffic).
        Without this, IP-only sightings would extract fine but never
        surface as a trackable asset - the gap flagged in review.
        """
        neighbors = graph_engine.neighbors(EntityType.IP_ADDRESS, ip)
        hostnames: List[str] = []
        mac_addresses: List[str] = []
        usernames: List[str] = []

        for n in neighbors:
            node = n["node"]
            if node.get("entity_type") == EntityType.HOSTNAME.value:
                hostnames.append(node["value"])
            elif node.get("entity_type") == EntityType.MAC_ADDRESS.value:
                mac_addresses.append(node["value"])
            elif node.get("entity_type") == EntityType.USERNAME.value:
                usernames.append(node["value"])

        existing = await self.repo.find_one(primary_identifier=ip, asset_type="device")
        payload: Dict[str, Any] = dict(
            asset_type="device",
            primary_identifier=ip,
            hostname=hostnames[0] if hostnames else None,
            ip_addresses=[ip],
            mac_addresses=sorted(set(mac_addresses)),
            usernames=sorted(set(usernames)),
            tags=["auto-discovered"],
        )
        if existing:
            return await self.repo.update(existing.id, **payload)
        return await self.repo.create(**payload)

    async def resolve_asset_for_username(self, username: str) -> Optional[Asset]:
        """Upsert a user-type asset anchored on a username, for log lines
        (e.g. auth logs) that reference a user without an associated
        hostname in the same batch.
        """
        neighbors = graph_engine.neighbors(EntityType.USERNAME, username)
        ip_addresses: List[str] = []
        hostnames: List[str] = []

        for n in neighbors:
            node = n["node"]
            if node.get("entity_type") == EntityType.IP_ADDRESS.value:
                ip_addresses.append(node["value"])
            elif node.get("entity_type") == EntityType.HOSTNAME.value:
                hostnames.append(node["value"])

        existing = await self.repo.find_one(primary_identifier=username, asset_type="user")
        payload: Dict[str, Any] = dict(
            asset_type="user",
            primary_identifier=username,
            hostname=hostnames[0] if hostnames else None,
            ip_addresses=sorted(set(ip_addresses)),
            usernames=[username],
            tags=["auto-discovered"],
        )
        if existing:
            return await self.repo.update(existing.id, **payload)
        return await self.repo.create(**payload)

    async def upsert_asset_from_context(
        self, hostname: str, context: Dict[str, Any], increment_failed_auth: bool = False
    ) -> Asset:
        """Upsert a host asset from an explicit context dict (as built by
        app/core/normalized_event_mapper.py from a Team 1 event) rather than
        purely from graph co-occurrence. New values are unioned with
        whatever the asset already has on file, never overwritten -
        repeated events about the same host accumulate IPs/MACs/users/tags
        instead of clobbering earlier sightings.
        """
        existing = await self.repo.find_one(primary_identifier=hostname, asset_type="host")

        ip_addresses = sorted(set(context.get("ip_addresses", [])) | set(existing.ip_addresses if existing else []))
        mac_addresses = sorted(set(context.get("mac_addresses", [])) | set(existing.mac_addresses if existing else []))
        usernames = sorted(set(context.get("usernames", [])) | set(existing.usernames if existing else []))
        tags = sorted(set(context.get("tags", [])) | set(existing.tags if existing else []))
        metadata = {**(existing.metadata_json if existing else {}), **context.get("metadata_json", {})}
        failed_auth_count = (existing.failed_auth_count if existing else 0) + (1 if increment_failed_auth else 0)

        payload: Dict[str, Any] = dict(
            asset_type="host",
            primary_identifier=hostname,
            hostname=hostname,
            ip_addresses=ip_addresses,
            mac_addresses=mac_addresses,
            usernames=usernames,
            tags=tags,
            metadata_json=metadata,
            failed_auth_count=failed_auth_count,
        )
        if existing:
            return await self.repo.update(existing.id, **payload)
        return await self.repo.create(**payload)

    async def discover_from_entities(self, entities: List[Dict[str, Any]]) -> List[Asset]:
        """Given freshly extracted entities from one ingestion batch,
        resolve assets for every hostname seen, then also resolve
        standalone device (IP-anchored) and user (username-anchored)
        assets for entities that had no hostname co-occurring in this
        batch - so bare-IP firewall/IDS lines and hostname-less auth
        lines still produce a trackable asset instead of being silently
        dropped.
        """
        hostnames = [e for e in entities if e.get("entity_type") == EntityType.HOSTNAME.value]
        ips = [e for e in entities if e.get("entity_type") == EntityType.IP_ADDRESS.value]
        users = [e for e in entities if e.get("entity_type") == EntityType.USERNAME.value]

        assets: List[Asset] = []

        for h in hostnames:
            asset = await self.resolve_asset_for_hostname(h["value"])
            if asset:
                assets.append(asset)

        # Only fall back to a standalone device/user asset if this batch
        # had no hostname at all - if it did, resolve_asset_for_hostname
        # already folded these IPs/users into the host asset above.
        if not hostnames:
            for ip in {e["value"] for e in ips}:
                asset = await self.resolve_asset_for_ip(ip)
                if asset:
                    assets.append(asset)
            for user in {e["value"] for e in users}:
                asset = await self.resolve_asset_for_username(user)
                if asset:
                    assets.append(asset)

        return assets
