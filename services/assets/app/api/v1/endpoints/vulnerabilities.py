from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, verify_api_key
from app.core.exceptions import NotFoundError
from app.repositories.vulnerability_repository import VulnerabilityRepository
from app.schemas.common import PaginatedResponse
from app.schemas.vulnerability import VulnerabilityCreate, VulnerabilityRead
from app.services.vulnerability_enrichment_service import VulnerabilityEnrichmentService

router = APIRouter(prefix="/vulnerabilities", tags=["vulnerabilities"], dependencies=[Depends(verify_api_key)])


@router.get("", response_model=PaginatedResponse[VulnerabilityRead])
async def list_vulnerabilities(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    severity: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    repo = VulnerabilityRepository(db)
    filters = {"severity": severity} if severity else {}
    items = await repo.list(limit=page_size, offset=(page - 1) * page_size, **filters)
    total = await repo.count(**filters)
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{vuln_id}", response_model=VulnerabilityRead)
async def get_vulnerability(vuln_id: UUID, db: AsyncSession = Depends(get_db)):
    repo = VulnerabilityRepository(db)
    vuln = await repo.get(vuln_id)
    if not vuln:
        raise NotFoundError("Vulnerability not found")
    return vuln


@router.post("", response_model=VulnerabilityRead, status_code=201)
async def create_vulnerability(
    payload: VulnerabilityCreate,
    db: AsyncSession = Depends(get_db)
):
    service = VulnerabilityEnrichmentService(db)

    result = await service.enrich_cve(
        cve_id=payload.cve_id,
        asset_id=payload.asset_id,
        severity=payload.severity,
        cvss_score=payload.cvss_score,
        description=payload.description,
        affected_component=payload.affected_component,
        references=payload.references,
    )

    repo = VulnerabilityRepository(db)

    record = await repo.find_one(
        cve_id=result["cve_id"]
    )

    return record
