"""
Explainable graph analytics.

Every score returned here is paired with a plain-language reason and an
analytical interpretation drawn from a fixed, cautious vocabulary. Nothing
in this module ever labels a person a criminal or leader -- see
app/analytics/labels.py for the shared terminology contract.
"""
import networkx as nx


def compute_centrality(graph: nx.MultiGraph) -> dict[str, dict]:
    if graph.number_of_nodes() == 0:
        return {}

    simple = nx.Graph(graph)  # collapse parallel edges for standard centrality algorithms

    degree = nx.degree_centrality(simple)
    betweenness = nx.betweenness_centrality(simple) if simple.number_of_nodes() > 2 else {n: 0.0 for n in simple.nodes}
    closeness = nx.closeness_centrality(simple)
    try:
        pagerank = nx.pagerank(simple, max_iter=200)
    except nx.PowerIterationFailedConvergence:
        pagerank = {n: 1 / simple.number_of_nodes() for n in simple.nodes}

    results: dict[str, dict] = {}
    for node in simple.nodes:
        results[node] = {
            "degree_centrality": round(degree.get(node, 0), 4),
            "betweenness_centrality": round(betweenness.get(node, 0), 4),
            "closeness_centrality": round(closeness.get(node, 0), 4),
            "pagerank": round(pagerank.get(node, 0), 4),
            "connections": simple.degree(node),
        }
    return results


def explain_entity_score(node_id: str, label: str, metrics: dict, related_case_count: int, community_bridge: bool,
                          graph_size: int = 1) -> dict:
    """Produce the human-readable "Network Connectivity" card described in
    brief section F, e.g. 'Person P-102 -- Network Connectivity 87/100'.

    graph_size normalizes pagerank (whose values sum to 1 across all nodes,
    so raw pagerank shrinks as the graph grows) into a 0-1-ish signal: an
    "average" node in an N-node graph has pagerank ~= 1/N, so
    pagerank * graph_size centers an average node near 1.0 and a hub above
    it, without the score blowing past 100 for every node in a large graph.
    """
    normalized_pagerank = min(1.0, metrics.get("pagerank", 0) * max(graph_size, 1))
    connectivity_score = min(100, round(
        metrics.get("degree_centrality", 0) * 50
        + metrics.get("betweenness_centrality", 0) * 35
        + normalized_pagerank * 15
    ))

    reasons = [f"Connected to {metrics.get('connections', 0)} entities in this network view."]
    if related_case_count > 1:
        reasons.append(f"Appears across {related_case_count} cases.")
    if community_bridge:
        reasons.append("Acts as a bridge between at least two network communities.")
    if metrics.get("betweenness_centrality", 0) > 0.15:
        reasons.append("High betweenness centrality: many shortest paths in the network pass through this entity.")

    if connectivity_score >= 75:
        finding_label = "Analytical lead"
        interpretation = "High connectivity detected. Investigator verification recommended."
    elif connectivity_score >= 45:
        finding_label = "Risk indicator"
        interpretation = "Moderate connectivity detected. Consider reviewing linked entities and evidence."
    else:
        finding_label = "Potential connection"
        interpretation = "Limited connectivity in the current network view. May still be relevant to the investigation."

    return {
        "entity_id": node_id,
        "entity_label": label,
        "network_connectivity_score": connectivity_score,
        "score_out_of": 100,
        "reasons": reasons,
        "finding_label": finding_label,
        "analytical_interpretation": interpretation,
        "disclaimer": "This score reflects structural position within the supplied data only. It is not evidence of wrongdoing and requires investigator verification.",
    }


def identify_bridge_entities(graph: nx.MultiGraph, communities: dict[str, int]) -> list[str]:
    """An entity is a 'Potential Bridge Entity' if its immediate neighbors
    span more than one detected community."""
    simple = nx.Graph(graph)
    bridges = []
    for node in simple.nodes:
        neighbor_communities = {communities.get(neighbor) for neighbor in simple.neighbors(node)}
        neighbor_communities.discard(None)
        if len(neighbor_communities) > 1:
            bridges.append(node)
    return bridges
