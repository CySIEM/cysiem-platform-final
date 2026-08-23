"""Lightweight span-timing helper. Swap for OpenTelemetry SDK spans if/when
Layer 9's observability stack is stood up.
"""
import time
from contextlib import contextmanager

from app.core.logging import get_logger

logger = get_logger("cysiem.layer3.tracing")


@contextmanager
def span(name: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.debug("span", name=name, duration_ms=duration_ms)
