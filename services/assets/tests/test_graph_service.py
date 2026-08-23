from app.core.constants import EdgeType, EntityType
from app.core.graph_engine import GraphEngine


def test_add_entity_and_edge():
    graph = GraphEngine()
    graph.add_edge(
        EntityType.IP_ADDRESS, "10.0.0.1", EntityType.HOSTNAME, "HOST-A", EdgeType.IP_TO_HOSTNAME
    )
    stats = graph.stats()
    assert stats["nodes"] == 2
    assert stats["edges"] == 1


def test_neighbors_returns_linked_node():
    graph = GraphEngine()
    graph.add_edge(
        EntityType.IP_ADDRESS, "10.0.0.2", EntityType.HOSTNAME, "HOST-B", EdgeType.IP_TO_HOSTNAME
    )
    neighbors = graph.neighbors(EntityType.IP_ADDRESS, "10.0.0.2")
    assert len(neighbors) == 1
    assert neighbors[0]["node"]["value"] == "HOST-B"
