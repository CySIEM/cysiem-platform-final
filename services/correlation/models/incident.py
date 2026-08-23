from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class Incident:
    target: str
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""
