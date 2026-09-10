"""Build a NetworkX graph from the relational database for a case or an
entity neighborhood, and serialize it into Cytoscape.js-ready JSON."""
import networkx as nx
from sqlalchemy.orm import Session

from app.models.relationship import Relationship
from app.services.entity_service import ENTITY_TABLES


def _display_name(db: Session, entity_id: str, entity_type: str) -> str:
    model = ENTITY_TABLES.get(entity_type)
    if not model:
        return entity_id
    record = db.get(model, entity_id)
    if not record:
        return entity_id
    for attr in ("name", "registration", "number", "masked_number"):
        if hasattr(record, attr):
            return getattr(record, attr)
    return entity_id


def build_case_graph(db: Session, case_id: str) -> nx.MultiGraph:
    """A MultiGraph so repeated relation types between the same pair (e.g.
    multiple CALLED edges) are preserved as distinct, countable edges."""
    graph = nx.MultiGraph()
    edges = db.query(Relationship).filter(Relationship.case_id == case_id).all()

    for edge in edges:
        for node_id, node_type in ((edge.source_id, edge.source_type), (edge.target_id, edge.target_type)):
            if not graph.has_node(node_id):
                graph.add_node(node_id, type=node_type, label=_display_name(db, node_id, node_type))
        graph.add_edge(
            edge.source_id, edge.target_id,
            key=edge.id,
            relation_type=edge.relation_type,
            date=edge.occurred_on.isoformat(),
            frequency=edge.frequency,
            source=edge.source,
            confidence=edge.confidence,
            evidence=edge.evidence,
        )
    return graph


def build_entity_neighborhood_graph(db: Session, entity_id: str, depth: int = 1) -> nx.MultiGraph:
    """BFS outward from a single entity up to `depth` hops."""
    graph = nx.MultiGraph()
    frontier = {entity_id}
    visited = set()

    for _ in range(max(1, depth)):
        if not frontier:
            break
        edges = db.query(Relationship).filter(
            (Relationship.source_id.in_(frontier)) | (Relationship.target_id.in_(frontier))
        ).all()
        next_frontier = set()
        for edge in edges:
            for node_id, node_type in ((edge.source_id, edge.source_type), (edge.target_id, edge.target_type)):
                if not graph.has_node(node_id):
                    graph.add_node(node_id, type=node_type, label=_display_name(db, node_id, node_type))
                if node_id not in visited:
                    next_frontier.add(node_id)
            graph.add_edge(
                edge.source_id, edge.target_id,
                key=edge.id,
                relation_type=edge.relation_type,
                date=edge.occurred_on.isoformat(),
                frequency=edge.frequency,
                source=edge.source,
                confidence=edge.confidence,
                evidence=edge.evidence,
            )
        visited |= frontier
        frontier = next_frontier - visited

    if entity_id not in graph:
        graph.add_node(entity_id, type="UNKNOWN", label=entity_id)
    return graph


def to_cytoscape(graph: nx.MultiGraph, metrics: dict | None = None, communities: dict | None = None) -> dict:
    metrics = metrics or {}
    communities = communities or {}
    nodes = []
    for node_id, attrs in graph.nodes(data=True):
        node_metrics = metrics.get(node_id, {})
        nodes.append({
            "data": {
                "id": node_id,
                "label": attrs.get("label", node_id),
                "type": attrs.get("type", "UNKNOWN"),
                "connections": graph.degree(node_id),
                "community": communities.get(node_id),
                **node_metrics,
            }
        })

    edges = []
    seen_multi: dict[tuple, int] = {}
    for source, target, key, attrs in graph.edges(keys=True, data=True):
        pair = tuple(sorted((source, target)))
        seen_multi[pair] = seen_multi.get(pair, 0) + 1
        edges.append({
            "data": {
                "id": f"{source}->{target}#{attrs.get('key', key)}",
                "source": source,
                "target": target,
                "relation_type": attrs.get("relation_type"),
                "date": attrs.get("date"),
                "frequency": attrs.get("frequency"),
                "source_ref": attrs.get("source"),
                "confidence": attrs.get("confidence"),
                "evidence": attrs.get("evidence"),
                "parallel_index": seen_multi[pair],
            }
        })

    return {"nodes": nodes, "edges": edges, "node_count": len(nodes), "edge_count": len(edges)}
