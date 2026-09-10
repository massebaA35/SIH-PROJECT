"""
Network Time Machine: how a case's (or the whole dataset's) network looked
before, during, and after a selected date range.

This is a purely structural, cumulative-network comparison over the
`occurred_on` timestamps already recorded on each relationship -- it does
not predict or infer anything about real-world behavior, only reports how
the *recorded* graph's shape changed across the selected window.
"""
from datetime import date

from sqlalchemy.orm import Session

import networkx as nx

from app.analytics.community import detect_communities
from app.models.relationship import Relationship

MIN_DATE = date(2000, 1, 1)
MAX_DATE = date(2100, 1, 1)


def get_date_bounds(db: Session, case_id: str | None = None) -> dict:
    q = db.query(Relationship.occurred_on)
    if case_id:
        q = q.filter(Relationship.case_id == case_id)
    dates = sorted(r[0] for r in q.all())
    if not dates:
        return {"earliest": None, "latest": None}
    return {"earliest": dates[0].isoformat(), "latest": dates[-1].isoformat()}


def _build_graph(edges: list[Relationship]) -> nx.MultiGraph:
    graph = nx.MultiGraph()
    for edge in edges:
        graph.add_node(edge.source_id, type=edge.source_type)
        graph.add_node(edge.target_id, type=edge.target_type)
        graph.add_edge(edge.source_id, edge.target_id, key=edge.id, relation_type=edge.relation_type, date=edge.occurred_on.isoformat())
    return graph


def _snapshot(graph: nx.MultiGraph) -> dict:
    communities, _summary = detect_communities(graph)
    community_count = len(set(communities.values())) if communities else 0
    return {
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
        "community_count": community_count,
        "nodes": set(graph.nodes),
        "edge_ids": {attrs.get("key") for _, _, attrs in graph.edges(data=True)},
    }


def analyze_period(db: Session, start_date: date, end_date: date, case_id: str | None = None) -> dict:
    q = db.query(Relationship)
    if case_id:
        q = q.filter(Relationship.case_id == case_id)
    all_edges = q.all()

    before_edges = [e for e in all_edges if e.occurred_on < start_date]
    during_edges = [e for e in all_edges if start_date <= e.occurred_on <= end_date]
    after_edges = [e for e in all_edges if e.occurred_on <= end_date]  # cumulative through end of period

    before_graph = _build_graph(before_edges)
    during_graph = _build_graph(during_edges)
    after_graph = _build_graph(after_edges)

    before_snap = _snapshot(before_graph)
    during_snap = _snapshot(during_graph)
    after_snap = _snapshot(after_graph)

    new_entities = sorted(after_snap["nodes"] - before_snap["nodes"])
    new_relationships = sorted(during_snap["edge_ids"])
    # Entities that were part of the network before the window but generated
    # no recorded relationship activity during it -- an operational
    # definition of "quiet" rather than a claim the entity disappeared.
    dormant_entities = sorted(before_snap["nodes"] - during_snap["nodes"])

    community_delta = after_snap["community_count"] - before_snap["community_count"]
    if community_delta > 0:
        community_finding = f"Possible community split: community count increased from {before_snap['community_count']} to {after_snap['community_count']}."
    elif community_delta < 0:
        community_finding = f"Possible community merge: community count decreased from {before_snap['community_count']} to {after_snap['community_count']}."
    else:
        community_finding = f"No material change in community structure ({after_snap['community_count']} communities before and after)."

    if len(new_relationships) > 0:
        expansion_finding = f"Network expansion detected: {len(new_relationships)} new relationship(s) appeared during the selected period."
    else:
        expansion_finding = "No new relationships were recorded during the selected period."

    return {
        "case_id": case_id,
        "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "before": {"node_count": before_snap["node_count"], "edge_count": before_snap["edge_count"], "community_count": before_snap["community_count"]},
        "during": {"node_count": during_snap["node_count"], "edge_count": during_snap["edge_count"], "community_count": during_snap["community_count"]},
        "after": {"node_count": after_snap["node_count"], "edge_count": after_snap["edge_count"], "community_count": after_snap["community_count"]},
        "new_entities": new_entities,
        "new_relationship_count": len(new_relationships),
        "dormant_entities": dormant_entities,
        "findings": [expansion_finding, community_finding],
        "disclaimer": "This comparison reflects structural changes in the recorded dataset only. It is not a prediction of real-world behavior.",
    }
