"""Explainable graph analytics for the synthetic NETRA prototype."""
from typing import Any
import networkx as nx


def _pagerank(graph: nx.Graph) -> dict[str, float]:
    try:
        return nx.pagerank(graph)
    except ModuleNotFoundError:
        # Keep the fallback usable when SciPy is not installed.
        node_count = max(len(graph), 1)
        scores = {node: 1 / node_count for node in graph}
        for _ in range(20):
            updated = {}
            for node in graph:
                inbound = sum(scores[neighbor] / max(graph.degree(neighbor), 1) for neighbor in graph.neighbors(node))
                updated[node] = 0.15 / node_count + 0.85 * inbound
            scores = updated
        return scores


def calculate_metrics(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    graph = nx.Graph()
    graph.add_nodes_from(node["id"] for node in nodes)
    graph.add_edges_from((edge["source"], edge["target"]) for edge in edges)
    if not graph:
        return {}
    pagerank = _pagerank(graph)
    return {
        node_id: {
            "degree": round(value, 3),
            "betweenness": round(nx.betweenness_centrality(graph).get(node_id, 0), 3),
            "closeness": round(nx.closeness_centrality(graph).get(node_id, 0), 3),
            "pagerank": round(pagerank.get(node_id, 0), 3),
        }
        for node_id, value in nx.degree_centrality(graph).items()
    }
