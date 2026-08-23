from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, verify_api_key
from app.core.exceptions import NotFoundError
from app.repositories.ioc_repository import IOCRepository
from app.schemas.common import PaginatedResponse
from app.schemas.ioc import IOCCreate, IOCRead
from app.services.threat_intel_service import ThreatIntelService

router = APIRouter(prefix="/iocs", tags=["iocs"], dependencies=[Depends(verify_api_key)])


@router.get("", response_model=PaginatedResponse[IOCRead])
async def list_iocs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    is_malicious: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    repo = IOCRepository(db)
    filters = {"is_malicious": is_malicious} if is_malicious is not None else {}
    items = await repo.list(limit=page_size, offset=(page - 1) * page_size, **filters)
    total = await repo.count(**filters)
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{ioc_id}", response_model=IOCRead)
async def get_ioc(ioc_id: UUID, db: AsyncSession = Depends(get_db)):
    repo = IOCRepository(db)
    ioc = await repo.get(ioc_id)
    if not ioc:
        raise NotFoundError("IOC not found")
    return ioc


@router.post("", response_model=IOCRead, status_code=201)
async def create_ioc(payload: IOCCreate, db: AsyncSession = Depends(get_db)):
    repo = IOCRepository(db)
    return await repo.create(**payload.model_dump())


@router.post("/sync")
async def sync_threat_intel(db: AsyncSession = Depends(get_db)):
    service = ThreatIntelService(db)
    return await service.sync_feeds()
