import networkx as nx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.analytics.centrality import compute_centrality, explain_entity_score, identify_bridge_entities
from app.analytics.community import detect_communities
from app.ai.entity_resolution import find_possible_duplicate_persons
from app.graph.graph_builder import build_case_graph, build_entity_neighborhood_graph
from app.models.relationship import Relationship
from app.models.user import User
from app.security.audit_chain import record_event
from app.security.rbac import get_current_user
from app.services.entity_service import get_entity_detail, list_entities

router = APIRouter(prefix="/api/entities", tags=["entities"])


class ResolutionDecisionRequest(BaseModel):
    entity_a: str = Field(max_length=20)
    entity_b: str = Field(max_length=20)
    decision: str = Field(pattern="^(CONFIRMED|DISMISSED)$")
    note: str = Field(default="", max_length=1000)


@router.get("")
def entities(
    type: str | None = Query(default=None, alias="type"),
    q: str = "",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return list_entities(db, type, q, page, page_size)


@router.get("/resolution/duplicates")
def entity_resolution_candidates(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    """Possible duplicate PERSON records. Never auto-merged -- see brief section 11."""
    return {"candidates": find_possible_duplicate_persons(db)}


@router.post("/resolution/decision")
def record_resolution_decision(payload: ResolutionDecisionRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Record an investigator's Confirm Match / Keep Separate decision on a
    potential-duplicate pair. This never merges records automatically --
    it only logs the human decision to the tamper-evident audit trail so
    there's a durable record of who reviewed which candidate and when."""
    record_event(
        db, "ENTITY_RESOLUTION_DECISION",
        {"entity_a": payload.entity_a, "entity_b": payload.entity_b, "decision": payload.decision, "note": payload.note},
        user_id=user.id, username=user.username,
    )
    return {"status": "recorded", "entity_a": payload.entity_a, "entity_b": payload.entity_b, "decision": payload.decision}


@router.get("/{entity_id}")
def entity_detail(entity_id: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    detail = get_entity_detail(db, entity_id)
    if not detail:
        raise HTTPException(404, "Entity not found")

    # Score the entity within the real network(s) it belongs to (its case
    # graphs), not a 1-hop "star" centered on itself -- an entity is
    # trivially the most central node of its own ego-network, which would
    # make every entity in the dataset score as maximally connected.
    related_cases = detail["related_cases"]
    if related_cases:
        case_graphs = [build_case_graph(db, case_id) for case_id in related_cases]
        graph = nx.compose_all(case_graphs) if len(case_graphs) > 1 else case_graphs[0]
    else:
        graph = build_entity_neighborhood_graph(db, entity_id, depth=2)
    metrics = compute_centrality(graph)
    communities, _summary = detect_communities(graph)
    bridges = set(identify_bridge_entities(graph, communities))
    scoring = explain_entity_score(
        entity_id, detail["label"], metrics.get(entity_id, {}), len(detail["related_cases"]), entity_id in bridges,
        graph.number_of_nodes(),
    )

    edges = db.query(Relationship).filter(
        (Relationship.source_id == entity_id) | (Relationship.target_id == entity_id)
    ).order_by(Relationship.occurred_on.desc()).limit(20).all()

    return {
        **detail,
        "score": scoring["network_connectivity_score"],
        "score_label": "Risk indicator",
        "insight": scoring["analytical_interpretation"] + " " + " ".join(scoring["reasons"]),
        "insight_label": scoring["finding_label"],
        "metrics": metrics.get(entity_id, {}),
        "evidence": [
            {"id": e.id, "relation": e.relation_type, "evidence": e.evidence, "timestamp": e.occurred_on.isoformat(), "confidence": e.confidence}
            for e in edges
        ],
    }
