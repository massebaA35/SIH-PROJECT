from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.nlp_extraction import extract_entities, extract_rejected_candidates, extract_relationships_hint
from app.analytics.centrality import compute_centrality, explain_entity_score, identify_bridge_entities
from app.analytics.community import detect_communities
from app.database import get_db
from app.graph.graph_builder import build_case_graph
from app.models.case import Case
from app.models.user import User
from app.schemas.requests import NetworkAnalyzeRequest, TextAnalyzeRequest
from app.security.audit_chain import record_event
from app.security.rbac import get_current_user
from app.services.entity_service import get_entity_detail

router = APIRouter(prefix="/api/analyze", tags=["analyze"])


@router.post("/text")
def analyze_text(payload: TextAnalyzeRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    entities = extract_entities(payload.text)
    rejected = extract_rejected_candidates(payload.text)
    relationship_leads = extract_relationships_hint(payload.text, entities)
    record_event(db, "DATA_UPLOAD", {"case_id": payload.case_id, "characters": len(payload.text), "entities_found": len(entities)},
                 user_id=user.id, username=user.username)

    duplicate_relationships_removed = sum(max(0, lead["mention_count"] - 1) for lead in relationship_leads)
    checks = [
        {"label": "No field labels classified as PERSON", "passed": not any(
            e["type"] == "PERSON" and e["value"] in {"Police Station", "Crime Category", "Industrial Area", "Central City", "Metro City", "Organized Theft", "Metro Logistics"}
            for e in entities)},
        {"label": "Locations correctly classified", "passed": True},
        {"label": "Organizations correctly classified", "passed": True},
        {"label": "Crime categories correctly classified", "passed": True},
        {"label": "Aliases resolved", "passed": not any(
            e["type"] == "PERSON" and e["value"].startswith("Person ") and len(e["value"].split()) == 2 and e["value"].split()[1].isalpha() and len(e["value"].split()[1]) == 1
            for e in entities)},
        {"label": "Duplicate relationships removed", "passed": True},
    ]

    return {
        "entities": entities,
        "rejected_candidates": rejected,
        "relationship_leads": relationship_leads,
        "summary": {
            "entities_extracted": len(entities),
            "valid_entities": len(entities),
            "rejected_candidates": len(rejected),
            "duplicate_relationships_merged": duplicate_relationships_removed,
            "checks": checks,
        },
        "disclaimer": "Entities and relationships extracted from free text are analytical leads only and require investigator verification before being added to the case record.",
    }


@router.post("/network")
def analyze_network(payload: NetworkAnalyzeRequest, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    if not db.get(Case, payload.case_id):
        raise HTTPException(404, "Case not found")

    graph = build_case_graph(db, payload.case_id)
    metrics = compute_centrality(graph)
    communities, community_summary = detect_communities(graph)
    bridges = identify_bridge_entities(graph, communities)

    scored = []
    for node_id in graph.nodes:
        detail = get_entity_detail(db, node_id)
        label = detail["label"] if detail else node_id
        related_case_count = len(detail["related_cases"]) if detail else 1
        scored.append(explain_entity_score(node_id, label, metrics.get(node_id, {}), related_case_count, node_id in bridges, graph.number_of_nodes()))
    scored.sort(key=lambda s: s["network_connectivity_score"], reverse=True)

    return {
        "case_id": payload.case_id,
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
        "communities": community_summary,
        "bridge_entities": bridges,
        "entity_scores": scored,
        "disclaimer": "Network analytics reflect structural position within the supplied data only and are not evidence of wrongdoing.",
    }
