"""Computes and persists an asset's risk score from its associated
vulnerabilities and IOC matches.
"""
from __future__ import annotations

from typing import Any, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.risk_engine import RiskFactors, compute_risk_score, score_to_severity
from app.models.ioc import IOC
from app.models.risk_score import RiskScore
from app.models.vulnerability import Vulnerability
from app.repositories.asset_repository import AssetRepository


class RiskScoringService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.asset_repo = AssetRepository(session)

    async def score_asset(self, asset_id: str) -> Dict[str, Any]:
        vuln_result = await self.session.execute(
            select(Vulnerability).where(Vulnerability.asset_id == asset_id)
        )
        vulns = list(vuln_result.scalars().all())
        ioc_result = await self.session.execute(select(IOC).where(IOC.is_malicious == True))  # noqa: E712
        malicious_iocs = list(ioc_result.scalars().all())

        import uuid as _uuid

        asset = await self.asset_repo.get(_uuid.UUID(asset_id))

        factors = RiskFactors(
            critical_vulns=sum(1 for v in vulns if v.severity == "critical"),
            high_vulns=sum(1 for v in vulns if v.severity == "high"),
            medium_vulns=sum(1 for v in vulns if v.severity == "medium"),
            ioc_matches=len(malicious_iocs),
            # Populated by NormalizedEventIngestionService as real events
            # come in (see is_failed_event() in normalized_event_mapper.py) -
            # previously always 0 because nothing wrote to these counters.
            failed_auth_events=asset.failed_auth_count if asset else 0,
            unusual_processes=asset.unusual_process_count if asset else 0,
        )
        score = compute_risk_score(factors)
        severity = score_to_severity(score)

        if asset:
            await self.asset_repo.update(asset.id, risk_score=score, severity=severity)

        self.session.add(
            RiskScore(asset_id=asset_id, score=score, severity=severity, factors=factors.__dict__)
        )
        await self.session.flush()

        return {"asset_id": asset_id, "score": score, "severity": severity, "factors": factors.__dict__}
