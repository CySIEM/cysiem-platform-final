"""Maps CySIEMException subclasses (and unhandled exceptions) to
consistent JSON error responses.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import CySIEMException
from app.core.logging import get_logger

logger = get_logger("cysiem.layer3.errors")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(CySIEMException)
    async def handle_cysiem_exception(request: Request, exc: CySIEMException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def handle_unhandled_exception(request: Request, exc: Exception):
        logger.error("unhandled.exception", path=request.url.path, error=str(exc))
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
