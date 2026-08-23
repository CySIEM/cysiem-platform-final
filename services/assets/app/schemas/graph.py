from typing import Any, Dict, List

from pydantic import BaseModel


class GraphStats(BaseModel):
    nodes: int
    edges: int


class GraphNeighbor(BaseModel):
    node: Dict[str, Any]
    edge: Dict[str, Any]


class IngestLogRequest(BaseModel):
    raw_line: str


class IngestLogBatchRequest(BaseModel):
    lines: List[str]


class IngestResult(BaseModel):
    log_type: str
    entities_found: int
    entities: List[Dict[str, Any]]
