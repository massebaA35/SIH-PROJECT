from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.alert import Alert
from app.models.audit import AuditLog
from app.models.case import Case
from app.models.evidence import Evidence
from app.models.event import Event
from app.models.relationship import Relationship
from app.models.user import User
from app.security.rbac import get_current_user
from app.services.entity_service import get_entity_detail
from app.graph.graph_builder import build_case_graph
from app.analytics.centrality import compute_centrality, explain_entity_score, identify_bridge_entities
from app.analytics.community import detect_communities

router = APIRouter(prefix="/api/cases", tags=["cases"])


def _case_out(case: Case) -> dict:
    return {
        "id": case.id, "title": case.title, "category": case.category, "status": case.status,
        "priority": case.priority, "risk_level": case.risk_level, "region": case.region,
        "assigned_investigator": case.assigned_investigator, "opened_date": case.opened_date.isoformat(),
        "updated_at": case.updated_at.isoformat(),
    }


@router.get("")
def list_cases(
    search: str | None = None,
    status: str | None = None,
    category: str | None = None,
    priority: str | None = None,
    region: str | None = None,
    risk_level: str | None = None,
    sort_by: str = Query(default="opened_date", pattern="^(opened_date|title|priority|risk_level|status)$"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    q = db.query(Case)
    if search:
        like = f"%{search.lower()}%"
        q = q.filter((Case.title.ilike(like)) | (Case.id.ilike(like)) | (Case.description.ilike(like)))
    if status:
        q = q.filter(Case.status == status)
    if category:
        q = q.filter(Case.category == category)
    if priority:
        q = q.filter(Case.priority == priority)
    if region:
        q = q.filter(Case.region == region)
    if risk_level:
        q = q.filter(Case.risk_level == risk_level)

    total = q.count()
    column = getattr(Case, sort_by)
    q = q.order_by(column.desc() if sort_dir == "desc" else column.asc())
    items = q.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": [_case_out(c) for c in items],
        "total": total, "page": page, "page_size": page_size,
    }


@router.get("/{case_id}")
def case_detail(case_id: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(404, "Case not found")

    edges = db.query(Relationship).filter(Relationship.case_id == case_id).all()
    entity_ids = sorted({e.source_id for e in edges} | {e.target_id for e in edges})
    related_entities = [d for eid in entity_ids if (d := get_entity_detail(db, eid))]
    related_locations = [e for e in related_entities if e["type"] == "LOCATION"]

    events = db.query(Event).filter(Event.case_id == case_id).order_by(Event.timestamp.asc()).all()
    alerts = db.query(Alert).filter(Alert.case_id == case_id).all()
    evidence = db.query(Evidence).filter(Evidence.case_id == case_id).all()
    audit_history = db.query(AuditLog).filter(AuditLog.event_data.contains(case_id)).order_by(AuditLog.seq.desc()).limit(20).all()

    graph = build_case_graph(db, case_id)
    metrics = compute_centrality(graph)
    communities, _summary = detect_communities(graph)
    bridges = set(identify_bridge_entities(graph, communities))
    ai_insights = []
    for node_id in sorted(graph.nodes, key=lambda n: metrics.get(n, {}).get("degree_centrality", 0), reverse=True)[:5]:
        detail = next((d for d in related_entities if d["id"] == node_id), None)
        label = detail["label"] if detail else node_id
        related_case_count = len(detail["related_cases"]) if detail else 1
        ai_insights.append(explain_entity_score(node_id, label, metrics.get(node_id, {}), related_case_count, node_id in bridges, graph.number_of_nodes()))

    return {
        "case": _case_out(case),
        "description": case.description,
        "related_entities": related_entities,
        "related_locations": related_locations,
        "related_events": [
            {"id": e.id, "type": e.event_type, "title": e.title, "timestamp": e.timestamp.isoformat(), "description": e.description}
            for e in events
        ],
        "evidence": [
            {"id": e.id, "type": e.evidence_type, "description": e.description, "hash": e.sha256_hash, "uploaded_at": e.uploaded_at.isoformat(), "uploaded_by": e.uploaded_by}
            for e in evidence
        ],
        "timeline": [
            {"id": e.id, "type": e.event_type, "title": e.title, "timestamp": e.timestamp.isoformat()}
            for e in events
        ],
        "network_graph_endpoint": f"/api/graph/case/{case_id}",
        "ai_insights": ai_insights,
        "alerts": [
            {"id": a.id, "severity": a.severity, "label": a.label, "title": a.title, "evidence": a.evidence, "status": a.status}
            for a in alerts
        ],
        "audit_history": [
            {"event_type": a.event_type, "username": a.username, "timestamp": a.timestamp.isoformat()}
            for a in audit_history
        ],
    }
