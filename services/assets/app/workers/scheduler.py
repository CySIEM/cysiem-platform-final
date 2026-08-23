"""APScheduler-based background job scheduler, started from the FastAPI
lifespan in app/main.py so a separate worker process isn't required for
the threat intel sync job. Swap for Celery/arq if job volume grows.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings
from app.workers.threat_intel_sync import run_threat_intel_sync

scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    settings = get_settings()
    scheduler.add_job(
        run_threat_intel_sync,
        "interval",
        minutes=settings.threat_intel_sync_interval_minutes,
        id="threat_intel_sync",
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
