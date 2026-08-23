"""FastAPI application entrypoint for CySIEM Layer 3 - Asset Intelligence.

Run locally:    uvicorn app.main:app --reload
Run in Docker:   docker-compose up --build
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.database.base import Base
from app.database.session import engine
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.error_handler import register_exception_handlers
from app.middleware.logging_middleware import AccessLogMiddleware
from app.workers.scheduler import start_scheduler, stop_scheduler

settings = get_settings()
configure_logging()
logger = get_logger("cysiem.layer3.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dev convenience: auto-create tables. Use Alembic migrations in
    # staging/production instead (see alembic/ and README.md).
    if not settings.is_production:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    start_scheduler()
    logger.info("layer3.startup", env=settings.app_env)
    yield
    stop_scheduler()
    await engine.dispose()
    logger.info("layer3.shutdown")


app = FastAPI(
    title=settings.app_name,
    description=(
        "Team 2 - Asset Intelligence Fabric: entity extraction, asset "
        "discovery, user/device/IP mapping, vulnerability & threat "
        "indicator extraction for the CySIEM 10-layer architecture."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AccessLogMiddleware)
app.add_middleware(CorrelationIdMiddleware)

register_exception_handlers(app)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root():
    return {"service": settings.app_name, "docs": "/docs", "health": f"{settings.api_v1_prefix}/health"}
