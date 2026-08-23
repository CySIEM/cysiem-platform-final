"""Attaches a correlation/request ID to every request for tracing across
Layer 3 -> Layer 4 -> ... service calls, and echoes it back in the response.
"""
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

_HEADER = "X-Correlation-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get(_HEADER, str(uuid.uuid4()))
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
        response = await call_next(request)
        response.headers[_HEADER] = correlation_id
        structlog.contextvars.clear_contextvars()
        return response
