from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, verify_api_key
from app.core.exceptions import NotFoundError
from app.repositories.entity_repository import EntityRepository
from app.schemas.common import PaginatedResponse
from app.schemas.entity import EntityRead

router = APIRouter(prefix="/entities", tags=["entities"], dependencies=[Depends(verify_api_key)])


@router.get("", response_model=PaginatedResponse[EntityRead])
async def list_entities(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    entity_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    repo = EntityRepository(db)
    filters = {"entity_type": entity_type} if entity_type else {}
    items = await repo.list(limit=page_size, offset=(page - 1) * page_size, **filters)
    total = await repo.count(**filters)
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{entity_id}", response_model=EntityRead)
async def get_entity(entity_id: UUID, db: AsyncSession = Depends(get_db)):
    repo = EntityRepository(db)
    entity = await repo.get(entity_id)
    if not entity:
        raise NotFoundError("Entity not found")
    return entity
