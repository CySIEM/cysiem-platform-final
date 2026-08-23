"""Log source detection and normalization for firewall, IDS/IPS, Sysmon,
auth, and DNS logs, feeding into the Layer 3 entity extraction pipeline.
"""
from __future__ import annotations

import re
from typing import Dict

from app.core.constants import LogSourceType

_SIGNATURES: Dict[LogSourceType, re.Pattern] = {
    LogSourceType.FIREWALL: re.compile(r"\b(ACCEPT|DENY|DROP)\b.*(?:SRC|DST)=", re.IGNORECASE),
    LogSourceType.IDS: re.compile(r"\b(alert|signature|classtype|priority)\b", re.IGNORECASE),
    LogSourceType.SYSMON: re.compile(r"\b(EventID|Sysmon|ProcessGuid|Image=)\b", re.IGNORECASE),
    LogSourceType.AUTH: re.compile(r"\b(sshd|logon|logoff|authentication|failed password|accepted password)\b", re.IGNORECASE),
    LogSourceType.DNS: re.compile(r"\b(query|qtype|dns|resolved)\b", re.IGNORECASE),
}


def detect_log_type(raw_line: str) -> LogSourceType:
    """Best-effort detection of which log source a raw line came from."""
    for log_type, pattern in _SIGNATURES.items():
        if pattern.search(raw_line):
            return log_type
    return LogSourceType.UNKNOWN


def normalize(raw_line: str, log_type: LogSourceType) -> str:
    """Light normalization pass; entity extraction runs on the result.

    Kept intentionally simple (whitespace collapse) since entity extraction
    is regex-driven and source-agnostic. Extend per log_type as new fields
    need first-class parsing (e.g. structured Sysmon EventID handling).
    """
    return re.sub(r"\s+", " ", raw_line).strip()
