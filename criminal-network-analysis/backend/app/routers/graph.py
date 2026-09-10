from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.analytics.centrality import compute_centrality, identify_bridge_entities
from app.analytics.community import detect_communities
from app.graph.graph_builder import build_case_graph, build_entity_neighborhood_graph, to_cytoscape
from app.models.case import Case
from app.models.user import User
from app.security.rbac import get_current_user

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/case/{case_id}")
def graph_for_case(case_id: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    if not db.get(Case, case_id):
        raise HTTPException(404, "Case not found")

    graph = build_case_graph(db, case_id)
    metrics = compute_centrality(graph)
    communities, community_summary = detect_communities(graph)
    bridges = identify_bridge_entities(graph, communities)

    payload = to_cytoscape(graph, metrics, communities)
    payload.update({
        "case_id": case_id,
        "communities": community_summary,
        "bridge_entities": bridges,
        "depth": 1,
        "disclaimer": "Nodes and edges reflect structural patterns in the supplied data only and are not evidence of wrongdoing.",
    })
    return payload


@router.get("/entity/{entity_id}")
def graph_for_entity(entity_id: str, depth: int = Query(default=1, ge=1, le=3),
                      db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    graph = build_entity_neighborhood_graph(db, entity_id, depth=depth)
    metrics = compute_centrality(graph)
    communities, community_summary = detect_communities(graph)
    bridges = identify_bridge_entities(graph, communities)

    payload = to_cytoscape(graph, metrics, communities)
    payload.update({
        "entity_id": entity_id,
        "communities": community_summary,
        "bridge_entities": bridges,
        "depth": depth,
        "disclaimer": "Nodes and edges reflect structural patterns in the supplied data only and are not evidence of wrongdoing.",
    })
    return payload
