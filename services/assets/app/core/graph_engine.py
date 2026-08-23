"""In-memory NetworkX knowledge graph for asset/entity relationships.

Layer 3 builds this graph incrementally as logs are ingested; it backs
entity resolution (merging duplicate nodes referring to the same real
asset) and is queried by the API and by Layer 5 (Knowledge Fabric / RAG).
"""
from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx

from app.core.constants import EdgeType, EntityType


class GraphEngine:
    """Thread-safe wrapper around a directed NetworkX multigraph."""

    def __init__(self) -> None:
        self._graph = nx.MultiDiGraph()
        self._lock = threading.Lock()

    def add_entity(self, entity_type: EntityType, value: str, **attrs: Any) -> str:
        node_id = self._node_id(entity_type, value)
        with self._lock:
            if self._graph.has_node(node_id):
                self._graph.nodes[node_id].update(attrs)
                self._graph.nodes[node_id]["occurrences"] = (
                    self._graph.nodes[node_id].get("occurrences", 1) + 1
                )
            else:
                self._graph.add_node(
                    node_id, entity_type=entity_type.value, value=value, occurrences=1, **attrs
                )
        return node_id

    def add_edge(
        self,
        src_type: EntityType,
        src_value: str,
        dst_type: EntityType,
        dst_value: str,
        edge_type: EdgeType,
        **attrs: Any,
    ) -> Tuple[str, str]:
        src_id = self.add_entity(src_type, src_value)
        dst_id = self.add_entity(dst_type, dst_value)
        with self._lock:
            self._graph.add_edge(src_id, dst_id, key=edge_type.value, edge_type=edge_type.value, **attrs)
        return src_id, dst_id

    def neighbors(self, entity_type: EntityType, value: str) -> List[Dict[str, Any]]:
        node_id = self._node_id(entity_type, value)

        if not self._graph.has_node(node_id):
            return []

        neighbors = []

        # Outgoing edges: node -> neighbor
        for _, neighbor_id, data in self._graph.out_edges(node_id, data=True):
            neighbors.append({
                "node": self._graph.nodes[neighbor_id],
                "edge": data,
            })

        # Incoming edges: neighbor -> node
        for neighbor_id, _, data in self._graph.in_edges(node_id, data=True):
            neighbors.append({
                "node": self._graph.nodes[neighbor_id],
                "edge": data,
            })

        return neighbors

    def get_node(self, entity_type: EntityType, value: str) -> Optional[Dict[str, Any]]:
        node_id = self._node_id(entity_type, value)
        return dict(self._graph.nodes[node_id]) if self._graph.has_node(node_id) else None

    def stats(self) -> Dict[str, int]:
        with self._lock:
            return {"nodes": self._graph.number_of_nodes(), "edges": self._graph.number_of_edges()}

    def export_json(self) -> Dict[str, Any]:
        with self._lock:
            return nx.readwrite.json_graph.node_link_data(self._graph)

    @staticmethod
    def _node_id(entity_type: EntityType, value: str) -> str:
        return f"{entity_type.value}:{value.lower()}"


# Process-wide singleton; swap for a persisted graph store (e.g. Neo4j) as
# Layer 3 scales beyond a single instance.
graph_engine = GraphEngine()
