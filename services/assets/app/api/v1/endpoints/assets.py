from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, verify_api_key
from app.core.exceptions import NotFoundError
from app.repositories.asset_repository import AssetRepository
from app.schemas.asset import AssetCreate, AssetRead
from app.schemas.common import PaginatedResponse
from app.services.risk_scoring_service import RiskScoringService

router = APIRouter(prefix="/assets", tags=["assets"], dependencies=[Depends(verify_api_key)])


@router.get("", response_model=PaginatedResponse[AssetRead])
async def list_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    asset_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    repo = AssetRepository(db)
    filters = {"asset_type": asset_type} if asset_type else {}
    items = await repo.list(limit=page_size, offset=(page - 1) * page_size, **filters)
    total = await repo.count(**filters)
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{asset_id}", response_model=AssetRead)
async def get_asset(asset_id: UUID, db: AsyncSession = Depends(get_db)):
    repo = AssetRepository(db)
    asset = await repo.get(asset_id)
    if not asset:
        raise NotFoundError("Asset not found")
    return asset


@router.post("", response_model=AssetRead, status_code=201)
async def create_asset(payload: AssetCreate, db: AsyncSession = Depends(get_db)):
    repo = AssetRepository(db)
    return await repo.create(**payload.model_dump())


@router.post("/{asset_id}/risk-score")
async def rescore_asset(asset_id: UUID, db: AsyncSession = Depends(get_db)):
    service = RiskScoringService(db)
    return await service.score_asset(str(asset_id))
