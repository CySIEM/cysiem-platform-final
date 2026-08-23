"""Static MITRE ATT&CK technique lookup used to annotate assets/IOCs.

This is a deliberately small seed table (extend from the MITRE ATT&CK STIX
bundle as needed); it exists so Layer 3 can tag extracted indicators with a
technique ID even before Layer 4 (Detection Fabric) runs full inference.
"""
from __future__ import annotations

from typing import Dict, List, Optional

_KEYWORD_TO_TECHNIQUE: Dict[str, List[str]] = {
    "failed password": ["T1110"],           # Brute Force
    "accepted password": ["T1078"],         # Valid Accounts
    "powershell": ["T1059.001"],            # Command and Scripting Interpreter: PowerShell
    "scheduled task": ["T1053.005"],        # Scheduled Task
    "port scan": ["T1046"],                 # Network Service Discovery
    "dns tunnel": ["T1071.004"],            # Application Layer Protocol: DNS
    "lateral movement": ["T1021"],          # Remote Services
    "exfiltration": ["T1041"],              # Exfiltration Over C2 Channel
    "privilege escalation": ["T1068"],
    "registry": ["T1112"],                  # Modify Registry
}


def map_keywords_to_techniques(text: str) -> Optional[List[str]]:
    text_lower = text.lower()
    hits: List[str] = []
    for keyword, techniques in _KEYWORD_TO_TECHNIQUE.items():
        if keyword in text_lower:
            hits.extend(techniques)
    return sorted(set(hits)) or None
