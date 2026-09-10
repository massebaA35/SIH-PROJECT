"""Cross-table entity lookup, listing, filtering, and pagination."""
from sqlalchemy.orm import Session

from app.models.entities import Person, Organization, Vehicle, Phone, Location, Account
from app.models.relationship import Relationship

ENTITY_TABLES = {
    "PERSON": Person,
    "ORGANIZATION": Organization,
    "VEHICLE": Vehicle,
    "PHONE": Phone,
    "LOCATION": Location,
    "ACCOUNT": Account,
}

_DISPLAY_ATTR_ORDER = ("name", "registration", "number", "masked_number")


def display_name(record) -> str:
    for attr in _DISPLAY_ATTR_ORDER:
        if hasattr(record, attr):
            return getattr(record, attr)
    return record.id


def entity_type_from_id(entity_id: str) -> str | None:
    prefix = entity_id.split("-")[0].upper()
    return {
        "PERSON": "PERSON", "ORG": "ORGANIZATION", "VEHICLE": "VEHICLE",
        "PHONE": "PHONE", "LOC": "LOCATION", "ACCOUNT": "ACCOUNT",
    }.get(prefix)


def get_entity_detail(db: Session, entity_id: str) -> dict | None:
    entity_type = entity_type_from_id(entity_id)
    model = ENTITY_TABLES.get(entity_type) if entity_type else None
    if not model:
        return None
    record = db.get(model, entity_id)
    if not record:
        return None

    edges = db.query(Relationship).filter(
        (Relationship.source_id == entity_id) | (Relationship.target_id == entity_id)
    ).all()
    related_cases = sorted({e.case_id for e in edges if e.case_id})

    return {
        "id": record.id,
        "label": display_name(record),
        "type": entity_type,
        "connections": len(edges),
        "related_cases": related_cases,
        "first_seen": record.first_seen.isoformat() if getattr(record, "first_seen", None) else None,
        "last_seen": record.last_seen.isoformat() if getattr(record, "last_seen", None) else None,
        "source": getattr(record, "source", "Synthetic demo dataset"),
        "attributes": {c.name: getattr(record, c.name) for c in record.__table__.columns},
    }


def list_entities(db: Session, entity_type: str | None, query: str | None, page: int, page_size: int) -> dict:
    types_to_scan = [entity_type] if entity_type else list(ENTITY_TABLES.keys())
    results: list[dict] = []

    for t in types_to_scan:
        model = ENTITY_TABLES.get(t)
        if not model:
            continue
        for record in db.query(model).all():
            label = display_name(record)
            if query and query.lower() not in label.lower() and query.lower() not in record.id.lower():
                continue
            results.append({"id": record.id, "label": label, "type": t})

    results.sort(key=lambda r: r["id"])
    total = len(results)
    start = (page - 1) * page_size
    page_items = results[start:start + page_size]

    edge_counts: dict[str, int] = {}
    if page_items:
        ids = [item["id"] for item in page_items]
        edges = db.query(Relationship).filter(
            (Relationship.source_id.in_(ids)) | (Relationship.target_id.in_(ids))
        ).all()
        for e in edges:
            edge_counts[e.source_id] = edge_counts.get(e.source_id, 0) + 1
            edge_counts[e.target_id] = edge_counts.get(e.target_id, 0) + 1

    for item in page_items:
        item["connections"] = edge_counts.get(item["id"], 0)

    return {"items": page_items, "total": total, "page": page, "page_size": page_size}
