"""Hidden Link Discovery: find indirect paths between two entities across
the whole dataset, not just within one case, since the point of this
feature is surfacing connections that cross case boundaries."""
import networkx as nx

MAX_HOPS = 6
MAX_PATHS = 3


def find_paths(graph: nx.MultiGraph, entity_a: str, entity_b: str) -> list[dict]:
    if entity_a not in graph or entity_b not in graph:
        return []
    if entity_a == entity_b:
        return []

    try:
        simple_graph = nx.Graph(graph)  # collapse parallel edges for path search only
        all_paths = list(nx.all_simple_paths(simple_graph, entity_a, entity_b, cutoff=MAX_HOPS))
    except (nx.NodeNotFound, nx.NetworkXNoPath):
        return []
    if not all_paths:
        return []

    all_paths.sort(key=len)
    results = []
    for path in all_paths[:MAX_PATHS]:
        results.append(_describe_path(graph, path))
    return results


def _best_edge(graph: nx.MultiGraph, a: str, b: str) -> dict:
    """A MultiGraph can have several parallel edges between two nodes (e.g.
    multiple CALLED records); surface the highest-confidence one as the
    representative edge for this hop."""
    candidates = graph.get_edge_data(a, b) or {}
    if not candidates:
        return {}
    return max(candidates.values(), key=lambda attrs: attrs.get("confidence", 0))


def _describe_path(graph: nx.MultiGraph, path: list[str]) -> dict:
    nodes = [
        {"id": node_id, "type": graph.nodes[node_id].get("type", "UNKNOWN"), "label": graph.nodes[node_id].get("label", node_id)}
        for node_id in path
    ]
    edges = []
    confidences = []
    case_ids: set[str] = set()
    for a, b in zip(path, path[1:]):
        edge = _best_edge(graph, a, b)
        confidences.append(edge.get("confidence", 0.5))
        if edge.get("case_id"):
            case_ids.add(edge["case_id"])
        edges.append({
            "source": a, "target": b,
            "relation_type": edge.get("relation_type", "ASSOCIATED_WITH"),
            "date": edge.get("date"),
            "confidence": edge.get("confidence"),
            "evidence": edge.get("evidence", ""),
        })

    # Confidence decays with path length (a 6-hop chain is a weaker analytical
    # lead than a 2-hop one, even if every individual edge is solid) and is
    # bounded by the weakest link in the chain.
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
    length_penalty = max(0.5, 1 - 0.08 * (len(path) - 2))
    overall_confidence = round(min(avg_confidence, avg_confidence * length_penalty), 2)

    return {
        "hop_count": len(path) - 1,
        "nodes": nodes,
        "edges": edges,
        "confidence": overall_confidence,
        "spans_multiple_cases": len(case_ids) > 1,
        "related_cases": sorted(cid for cid in case_ids if cid),
        "label": "Analytical lead — requires investigator verification",
    }
