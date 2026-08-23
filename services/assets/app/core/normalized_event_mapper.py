"""Pure-logic mapping from a Team 1 NormalizedEvent into the entity/asset
shapes Layer 3 works with. No I/O here (no database, no network) - this is
what makes it possible to validate against a whole batch of real log
exports offline, which is exactly what scripts/validate_against_real_logs.py
does. Persistence lives in
app/services/normalized_event_ingestion_service.py.
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.core.constants import EntityType
from app.core.entity_extractor import ExtractedEntity, entity_extractor
from app.schemas.normalized_event import NormalizedEvent

# Outcomes that count as a failed operation for risk scoring. Covers both the
# Team 1 `outcome` field ("failure") and the raw auditd convention
# (`res=failed`) that sometimes only shows up in the free-text message.
_FAILURE_OUTCOMES = {"failure", "fail", "failed", "denied", "deny"}


def extract_entities(event: NormalizedEvent) -> List[ExtractedEntity]:
    """Combine high-confidence structured-field entities with a regex sweep
    over the free-text fields (message/raw/asset notes) for anything the
    structured fields don't carry - hashes, CVEs, domains, URLs, and MAC
    addresses (Team 1 currently only puts the MAC in the asset `notes`
    free-text field, not as a structured field).
    """
    entities: List[ExtractedEntity] = []
    norm = event.normalized
    src = event.source

    if src.host:
        entities.append(ExtractedEntity(EntityType.HOSTNAME, src.host, confidence=1.0, context="source.host"))
    if src.ip:
        entities.append(ExtractedEntity(EntityType.IP_ADDRESS, src.ip, confidence=1.0, context="source.ip"))
    if norm.user and not norm.user.isdigit():
        # Numeric-only "user" values are raw uids (e.g. "0"), not usernames -
        # keep them out of the username entity pool, they're not useful for
        # analyst-facing asset mapping.
        entities.append(ExtractedEntity(EntityType.USERNAME, norm.user, confidence=1.0, context="normalized.user"))
    if norm.process_name:
        entities.append(ExtractedEntity(EntityType.PROCESS, norm.process_name, confidence=1.0, context="normalized.process_name"))
    if norm.parent_process:
        entities.append(ExtractedEntity(EntityType.PROCESS, norm.parent_process, confidence=0.9, context="normalized.parent_process"))
    if norm.src_ip:
        entities.append(ExtractedEntity(EntityType.IP_ADDRESS, norm.src_ip, confidence=1.0, context="normalized.src_ip"))
    if norm.dest_ip:
        entities.append(ExtractedEntity(EntityType.IP_ADDRESS, norm.dest_ip, confidence=1.0, context="normalized.dest_ip"))
    if norm.src_port:
        entities.append(ExtractedEntity(EntityType.PORT, str(norm.src_port), confidence=0.9, context="normalized.src_port"))
    if norm.dest_port:
        entities.append(ExtractedEntity(EntityType.PORT, str(norm.dest_port), confidence=0.9, context="normalized.dest_port"))

    # Regex sweep for anything structured fields don't cover: MAC addresses
    # (only ever seen in asset.notes free text), plus any CVE/hash/domain/
    # URL/email that shows up in the message or raw payload. Deliberately
    # uses extract_narrative() (not extract()) - message/raw/notes are prose,
    # and the PORT/USERNAME keyword-matchers extract() also runs produce
    # false positives on prose ("a user performs..." -> username "performs").
    # user/ports are already covered by the structured fields above.
    for text in (norm.message, event.raw, _asset_notes(event)):
        if text:
            entities.extend(entity_extractor.extract_narrative(text))

    return _dedupe(entities)


def build_asset_context(event: NormalizedEvent) -> Dict[str, Any]:
    """Everything Layer 3 knows about the asset this event came from, ready
    to merge into an Asset row (tags/criticality/owner/segment are metadata
    Team 1 already computed - no reason to re-derive them).
    """
    src = event.source
    asset_ext = event.extensions.asset if event.extensions else None
    entities = extract_entities(event)

    mac_addresses = sorted({e.value for e in entities if e.entity_type == EntityType.MAC_ADDRESS})
    ip_addresses = sorted({e.value for e in entities if e.entity_type == EntityType.IP_ADDRESS})
    usernames = sorted({e.value for e in entities if e.entity_type == EntityType.USERNAME})

    tags = list(asset_ext.tags) if asset_ext and asset_ext.tags else []
    if src.source_type and src.source_type not in tags:
        tags.append(src.source_type)

    metadata: Dict[str, Any] = {}
    if asset_ext:
        if asset_ext.criticality:
            metadata["criticality"] = asset_ext.criticality
        if asset_ext.owner:
            metadata["owner"] = asset_ext.owner
        if asset_ext.asset_type:
            metadata["source_asset_type"] = asset_ext.asset_type
    if src.segment:
        metadata["segment"] = src.segment
    if src.collector:
        metadata["collector"] = src.collector
    if src.log_type:
        metadata["log_type"] = src.log_type

    return {
        "hostname": src.host,
        "ip_addresses": ip_addresses,
        "mac_addresses": mac_addresses,
        "usernames": usernames,
        "tags": tags,
        "metadata_json": metadata,
    }


def is_failed_event(event: NormalizedEvent) -> bool:
    """True if this event represents a failed operation - drives the
    failed_auth_events risk factor. Checks the structured `outcome` field
    first, then falls back to the auditd `res=failed` convention that shows
    up in the raw/message text when `outcome` itself is null.
    """
    outcome = (event.normalized.outcome or "").strip().lower()
    if outcome in _FAILURE_OUTCOMES:
        return True
    for text in (event.normalized.message, event.raw):
        if text and ("res=failed" in text.lower() or "result=fail" in text.lower()):
            return True
    return False


def _asset_notes(event: NormalizedEvent) -> str | None:
    if event.extensions and event.extensions.asset:
        return event.extensions.asset.notes
    return None


def _dedupe(entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
    seen = set()
    unique: List[ExtractedEntity] = []
    for e in entities:
        key = (e.entity_type, e.value.lower())
        if key not in seen:
            seen.add(key)
            unique.append(e)
    return unique
