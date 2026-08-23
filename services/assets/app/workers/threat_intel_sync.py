"""Standalone-runnable threat intel sync job.

Run directly with: python -m app.workers.threat_intel_sync
Also scheduled automatically by app/workers/scheduler.py at
THREAT_INTEL_SYNC_INTERVAL_MINUTES.
"""
import asyncio

from app.core.logging import get_logger
from app.database.session import async_session_factory
from app.services.threat_intel_service import ThreatIntelService

logger = get_logger("cysiem.layer3.worker.threat_intel_sync")


async def run_threat_intel_sync() -> None:
    async with async_session_factory() as session:
        service = ThreatIntelService(session)
        result = await service.sync_feeds()
        await session.commit()
        logger.info("threat_intel.sync.complete", imported=result["imported"])


if __name__ == "__main__":
    asyncio.run(run_threat_intel_sync())
