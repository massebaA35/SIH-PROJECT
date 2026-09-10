"""Global search across cases and every entity table."""
from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.relationship import Relationship
from app.services.entity_service import ENTITY_TABLES, display_name


def global_search(db: Session, query: str, types: list[str] | None = None) -> list[dict]:
    q = query.strip().lower()
    if not q:
        return []
    results: list[dict] = []

    if not types or "CASE" in [t.upper() for t in types]:
        for case in db.query(Case).all():
            if q in case.id.lower() or q in case.title.lower():
                results.append({
                    "id": case.id, "label": case.title, "type": "CASE",
                    "related_cases": [case.id], "connection_count": None,
                    "last_activity": case.updated_at.date().isoformat(),
                })

    entity_types = [t.upper() for t in types] if types else list(ENTITY_TABLES.keys())
    for entity_type in entity_types:
        model = ENTITY_TABLES.get(entity_type)
        if not model:
            continue
        for record in db.query(model).all():
            label = display_name(record)
            if q in record.id.lower() or q in label.lower():
                edges = db.query(Relationship).filter(
                    (Relationship.source_id == record.id) | (Relationship.target_id == record.id)
                ).all()
                related_cases = sorted({e.case_id for e in edges if e.case_id})
                results.append({
                    "id": record.id, "label": label, "type": entity_type,
                    "related_cases": related_cases, "connection_count": len(edges),
                    "last_activity": getattr(record, "last_seen", None).isoformat() if getattr(record, "last_seen", None) else None,
                })

    results.sort(key=lambda r: (r["type"] != "CASE", -(r.get("connection_count") or 0)))
    return results[:50]
