"""Parses the detection model's text response into a structured result.
Models occasionally wrap JSON in prose or code fences despite instructions,
so this extracts the first {...} block rather than requiring an exact-JSON
response. If nothing parseable comes back, falls back to simple keyword
heuristics over the event so the pipeline still produces a usable result.
"""
import json
import re
from typing import Any, Dict

_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)

_VALID_PREDICTIONS = {"benign", "suspicious", "malicious"}
_VALID_SEVERITIES = {"low", "medium", "high", "critical"}


def parse_model_response(text: str) -> Dict[str, Any]:
    match = _JSON_BLOCK.search(text or "")
    if match:
        try:
            data = json.loads(match.group(0))
            prediction = str(data.get("prediction", "suspicious")).lower()
            severity = str(data.get("severity", "medium")).lower()
            return {
                "prediction": prediction if prediction in _VALID_PREDICTIONS else "suspicious",
                "confidence": float(data.get("confidence", 0.5)),
                "severity": severity if severity in _VALID_SEVERITIES else "medium",
                "mitre": data.get("mitre") or "",
                "reason": data.get("reason") or text.strip()[:300],
            }
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    return _fallback_heuristic(text or "")


def _fallback_heuristic(text: str) -> Dict[str, Any]:
    """Used when the model didn't return parseable JSON at all - keeps the
    endpoint useful rather than erroring out on a malformed model response."""
    lowered = text.lower()
    if any(k in lowered for k in ("malicious", "attack", "compromise", "ransomware", "exfilt")):
        prediction, severity, confidence = "malicious", "high", 0.6
    elif any(k in lowered for k in ("suspicious", "anomal", "unusual", "failed")):
        prediction, severity, confidence = "suspicious", "medium", 0.4
    else:
        prediction, severity, confidence = "benign", "low", 0.3

    return {
        "prediction": prediction,
        "confidence": confidence,
        "severity": severity,
        "mitre": "",
        "reason": text.strip()[:300] or "Model returned no parseable classification; heuristic fallback applied.",
    }
