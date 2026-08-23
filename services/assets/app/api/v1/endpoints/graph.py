from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, verify_api_key
from app.core.constants import EntityType
from app.schemas.graph import GraphStats
from app.services.graph_service import GraphService

router = APIRouter(prefix="/graph", tags=["graph"], dependencies=[Depends(verify_api_key)])


@router.get("/stats", response_model=GraphStats)
async def graph_stats(db: AsyncSession = Depends(get_db)):
    service = GraphService(db)
    return service.stats()


@router.get("/export")
async def graph_export(db: AsyncSession = Depends(get_db)):
    service = GraphService(db)
    return service.export()


@router.get("/neighbors/{entity_type}/{value}")
async def graph_neighbors(entity_type: EntityType, value: str, db: AsyncSession = Depends(get_db)):
    from app.core.graph_engine import graph_engine

    return {"neighbors": graph_engine.neighbors(entity_type, value)}
