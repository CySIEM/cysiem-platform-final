"""Common interface for threat intel integrations. Each client runs in
'stub mode' (returns empty/deterministic results) when no credentials are
configured, so the service is fully runnable without external accounts.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class ThreatIntelClient(ABC):
    name: str = "base"

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        ...

    @abstractmethod
    async def lookup_ioc(self, ioc_type: str, value: str) -> Dict[str, Any]:
        """Return {'is_malicious': bool, 'confidence': float, 'source': str, 'raw': ...}"""

    @abstractmethod
    async def fetch_recent_indicators(self, limit: int = 50) -> List[Dict[str, Any]]:
        ...
