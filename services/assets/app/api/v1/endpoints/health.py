from fastapi import APIRouter, Response

from app.config import get_settings
from app.schemas.common import HealthResponse
from app.telemetry.metrics import metrics_response

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", service=settings.app_name, version="1.0.0")


@router.get("/metrics")
async def metrics() -> Response:
    return Response(content=metrics_response(), media_type="text/plain")
