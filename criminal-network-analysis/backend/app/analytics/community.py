"""Community detection using NetworkX's greedy modularity algorithm
(no extra dependency beyond networkx, deterministic given the same graph)."""
import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities


def detect_communities(graph: nx.MultiGraph) -> tuple[dict[str, int], list[dict]]:
    """Returns (node_id -> community index, [{id, label, members}])."""
    simple = nx.Graph(graph)
    if simple.number_of_nodes() < 2 or simple.number_of_edges() == 0:
        mapping = {node: 0 for node in simple.nodes}
        summary = [{"id": "COMMUNITY-0", "label": "Community 1", "members": list(simple.nodes)}] if simple.nodes else []
        return mapping, summary

    communities = list(greedy_modularity_communities(simple))
    mapping: dict[str, int] = {}
    summary: list[dict] = []
    for index, community in enumerate(communities):
        members = sorted(community)
        for member in members:
            mapping[member] = index
        summary.append({
            "id": f"COMMUNITY-{index}",
            "label": f"Community {index + 1}",
            "members": members,
            "size": len(members),
        })
    return mapping, summary
