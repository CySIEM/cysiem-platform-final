"""Simple weighted risk scoring for assets, based on associated IOCs,
vulnerabilities, and behavioral signal counts surfaced during Layer 3
enrichment. Layer 6 (Investigation) and Layer 9 (Dashboard) consume this.
"""
from __future__ import annotations

from dataclasses import dataclass

_WEIGHTS = {
    "critical_vuln": 25,
    "high_vuln": 15,
    "medium_vuln": 5,
    "ioc_match": 20,
    "failed_auth": 8,
    "unusual_process": 10,
}
_MAX_SCORE = 100


@dataclass
class RiskFactors:
    critical_vulns: int = 0
    high_vulns: int = 0
    medium_vulns: int = 0
    ioc_matches: int = 0
    failed_auth_events: int = 0
    unusual_processes: int = 0


def compute_risk_score(factors: RiskFactors) -> int:
    score = (
        factors.critical_vulns * _WEIGHTS["critical_vuln"]
        + factors.high_vulns * _WEIGHTS["high_vuln"]
        + factors.medium_vulns * _WEIGHTS["medium_vuln"]
        + factors.ioc_matches * _WEIGHTS["ioc_match"]
        + factors.failed_auth_events * _WEIGHTS["failed_auth"]
        + factors.unusual_processes * _WEIGHTS["unusual_process"]
    )
    return min(score, _MAX_SCORE)


def score_to_severity(score: int) -> str:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    return "low"
