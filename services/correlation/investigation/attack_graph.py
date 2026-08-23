from typing import Any, Dict, List


def build_attack_graph(alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create a graph using only observed alert entities and relations."""
    nodes = []
    edges = []

    for alert in alerts:
        if not isinstance(alert, dict):
            continue

        target = alert.get("target") or alert.get("host") or alert.get("device")
        source_ip = alert.get("source_ip")
        destination_ip = alert.get("destination_ip")
        user = alert.get("username")
        process = alert.get("process_name") or (alert.get("processes") or [None])[0]

        if target:
            nodes.append(str(target))
        if source_ip:
            nodes.append(str(source_ip))
        if destination_ip:
            nodes.append(str(destination_ip))
        if user:
            nodes.append(str(user))
        if process:
            nodes.append(str(process))

        if target and source_ip:
            edges.append((str(source_ip), str(target)))
        if target and destination_ip:
            edges.append((str(target), str(destination_ip)))
        if target and user:
            edges.append((str(user), str(target)))
        if target and process:
            edges.append((str(target), str(process)))

    unique_nodes = list(dict.fromkeys(nodes))
    unique_edges = list(dict.fromkeys(edges))

    return {
        "nodes": unique_nodes,
        "edges": unique_edges,
        "summary": "Attack path reconstructed from observed entities and relationships",
    }
