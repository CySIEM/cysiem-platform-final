"""Orchestrates raw log -> detected log type -> normalized text ->
extracted entities -> persisted Entity rows.
"""
from __future__ import annotations

from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.entity_extractor import ExtractedEntity, entity_extractor
from app.core.log_parsers import detect_log_type, normalize
from app.repositories.entity_repository import EntityRepository


class EntityExtractionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = EntityRepository(session)

    async def process_line(self, raw_line: str) -> tuple[str, List[ExtractedEntity]]:
        log_type = detect_log_type(raw_line)
        normalized = normalize(raw_line, log_type)
        entities = entity_extractor.extract(normalized)
        await self.persist_entities(entities, source_log_type=log_type.value)
        return log_type.value, entities

    async def persist_entities(self, entities: List[ExtractedEntity], source_log_type: str | None = None) -> None:
        """Upsert a list of already-extracted entities. Shared by the raw-line
        pipeline (process_line, above) and NormalizedEventIngestionService,
        which extracts entities from Team 1's structured JSON events instead
        of raw text - both paths land in the same entities table.
        """
        for entity in entities:
            existing = await self.repo.find_one(
                entity_type=entity.entity_type.value, value=entity.value
            )
            if existing:
                await self.repo.update(
                    existing.id, occurrences=existing.occurrences + 1, confidence=max(
                        existing.confidence, entity.confidence
                    )
                )
            else:
                await self.repo.create(
                    entity_type=entity.entity_type.value,
                    value=entity.value,
                    confidence=entity.confidence,
                    source_log_type=source_log_type,
                    context=entity.context,
                )

    async def process_batch(self, lines: List[str]) -> List[tuple[str, List[ExtractedEntity]]]:
        return [await self.process_line(line) for line in lines]
