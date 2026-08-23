"""Ingestion endpoint: accepts one or more raw log lines and runs the full
Layer 3 pipeline (extraction -> graph -> asset resolution -> IOC/vuln
enrichment) against them.
"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, verify_api_key
from app.schemas.graph import IngestLogBatchRequest, IngestLogRequest
from app.schemas.normalized_event import NormalizedEvent, NormalizedIngestResult
from app.services.ingestion_service import IngestionService
from app.services.normalized_event_ingestion_service import NormalizedEventIngestionService

router = APIRouter(prefix="/ingest", tags=["ingestion"], dependencies=[Depends(verify_api_key)])


@router.post("/line")
async def ingest_line(payload: IngestLogRequest, db: AsyncSession = Depends(get_db)):
    """Raw unstructured log text pipeline (regex-only, no upstream schema
    assumed). Use /ingest/events instead when Team 1's normalized JSON is
    available - it's higher-confidence and does less guessing.
    """
    service = IngestionService(db)
    return await service.ingest_line(payload.raw_line)


@router.post("/batch")
async def ingest_batch(payload: IngestLogBatchRequest, db: AsyncSession = Depends(get_db)):
    service = IngestionService(db)
    return {"results": await service.ingest_batch(payload.lines)}


@router.post("/events", response_model=NormalizedIngestResult)
async def ingest_normalized_events(payload: List[NormalizedEvent], db: AsyncSession = Depends(get_db)):
    """Ingest a batch of Team 1 normalized events - accepts exactly the JSON
    array shape Layer 2 exports (a plain list of event objects), so an
    export file can be POSTed here as-is.
    """
    service = NormalizedEventIngestionService(db)
    return await service.ingest_batch(payload)
