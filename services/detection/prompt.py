"""Builds the security-analysis prompt fed to the detection model."""
import json
from typing import Any, Dict, List

SYSTEM_PROMPT = """You are a cybersecurity threat detection engine analyzing
a single security event plus its known entity/asset context. Classify it
and respond with ONLY a JSON object, no other text, in exactly this shape:
{"prediction": "<benign|suspicious|malicious>", "confidence": <0.0-1.0>,
"severity": "<low|medium|high|critical>", "mitre": "<ATT&CK technique id
or empty string>", "reason": "<one sentence explanation>"}"""


def build_prompt(event: Dict[str, Any], entities: List[Any], assets: List[Any]) -> str:
    return (
        "Event:\n" + json.dumps(event, default=str) + "\n\n"
        "Known entities:\n" + json.dumps(entities, default=str) + "\n\n"
        "Known assets:\n" + json.dumps(assets, default=str) + "\n\n"
        "Classify this event."
    )
