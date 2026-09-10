"""
Investigator-facing AI assistant.

This assistant answers ONLY from the local synthetic dataset -- there is no
external LLM call, so nothing here can hallucinate facts not present in the
database. Intent is matched with simple, transparent keyword/regex rules
(no black-box model), and every answer that references data includes the
supporting entity/event ids so an investigator can verify it directly. If
no matching data exists, it says so explicitly rather than guessing.
"""
import re

from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.case import Case
from app.models.event import Event
from app.models.relationship import Relationship

NO_DATA_MESSAGE = "No supporting information was found in the available dataset."

CASE_ID_RE = re.compile(r"\bCASE-\d+\b", re.IGNORECASE)
ENTITY_ID_RE = re.compile(r"\b(?:PERSON|ORG|VEHICLE|PHONE|LOC|ACCOUNT)-\d+\b", re.IGNORECASE)


def _entity_display_name(db: Session, entity_id: str) -> str:
    from app.services.entity_service import ENTITY_TABLES, entity_type_from_id
    entity_type = entity_type_from_id(entity_id)
    model = ENTITY_TABLES.get(entity_type) if entity_type else None
    if not model:
        return entity_id
    record = db.get(model, entity_id)
    if not record:
        return entity_id
    for attr in ("name", "registration", "number", "masked_number"):
        if hasattr(record, attr):
            return getattr(record, attr)
    return entity_id


def _answer_case_entities(db: Session, case_id: str) -> dict:
    edges = db.query(Relationship).filter(Relationship.case_id == case_id).all()
    if not edges:
        return {"answer": NO_DATA_MESSAGE, "supporting": []}
    entities = sorted({e.source_id for e in edges} | {e.target_id for e in edges})
    named = [f"{eid} ({_entity_display_name(db, eid)})" for eid in entities]
    return {
        "answer": f"{len(entities)} entities are connected to {case_id}: {', '.join(named)}.",
        "supporting": entities,
    }


def _answer_strongest_connections(db: Session, entity_id: str) -> dict:
    edges = db.query(Relationship).filter(
        (Relationship.source_id == entity_id) | (Relationship.target_id == entity_id)
    ).all()
    if not edges:
        return {"answer": NO_DATA_MESSAGE, "supporting": []}
    ranked = sorted(edges, key=lambda e: e.frequency * e.confidence, reverse=True)[:5]
    lines = []
    for e in ranked:
        other = e.target_id if e.source_id == entity_id else e.source_id
        lines.append(f"{other} ({_entity_display_name(db, other)}) via {e.relation_type}, frequency {e.frequency}, confidence {round(e.confidence*100)}%")
    return {
        "answer": f"The strongest recorded connections of {entity_id} are: " + "; ".join(lines) + ". Requires investigator verification.",
        "supporting": [e.id for e in ranked],
    }


def _answer_multi_case_entities(db: Session) -> dict:
    edges = db.query(Relationship).filter(Relationship.case_id != "").all()
    per_entity: dict[str, set[str]] = {}
    for e in edges:
        per_entity.setdefault(e.source_id, set()).add(e.case_id)
        per_entity.setdefault(e.target_id, set()).add(e.case_id)
    multi = {eid: cases for eid, cases in per_entity.items() if len(cases) > 1}
    if not multi:
        return {"answer": NO_DATA_MESSAGE, "supporting": []}
    lines = [f"{eid} ({_entity_display_name(db, eid)}) -> {', '.join(sorted(cases))}" for eid, cases in multi.items()]
    return {
        "answer": f"{len(multi)} entities appear in more than one case: " + "; ".join(lines) + ". These are potential connections between cases and require investigator verification.",
        "supporting": list(multi.keys()),
    }


def _answer_why_flagged(db: Session, entity_id: str) -> dict:
    alerts = db.query(Alert).filter(Alert.entity_id == entity_id).all()
    if not alerts:
        return {"answer": NO_DATA_MESSAGE, "supporting": []}
    lines = [f"[{a.severity}/{a.label}] {a.title}: {a.evidence}" for a in alerts]
    return {
        "answer": f"{entity_id} has {len(alerts)} recorded alert(s): " + " | ".join(lines),
        "supporting": [a.id for a in alerts],
    }


def _answer_case_to_case(db: Session, case_a: str, case_b: str) -> dict:
    edges_a = db.query(Relationship).filter(Relationship.case_id == case_a).all()
    edges_b = db.query(Relationship).filter(Relationship.case_id == case_b).all()
    entities_a = {e.source_id for e in edges_a} | {e.target_id for e in edges_a}
    entities_b = {e.source_id for e in edges_b} | {e.target_id for e in edges_b}
    shared = sorted(entities_a & entities_b)
    if not shared:
        return {"answer": f"No shared entities were found between {case_a} and {case_b} in the available dataset.", "supporting": []}
    named = [f"{eid} ({_entity_display_name(db, eid)})" for eid in shared]
    return {
        "answer": f"{case_a} and {case_b} share {len(shared)} entities: {', '.join(named)}. This is a potential connection between cases and requires investigator verification.",
        "supporting": shared,
    }


def _answer_case_timeline_summary(db: Session, case_id: str) -> dict:
    events = db.query(Event).filter(Event.case_id == case_id).order_by(Event.timestamp.asc()).all()
    if not events:
        return {"answer": NO_DATA_MESSAGE, "supporting": []}
    counts: dict[str, int] = {}
    for e in events:
        counts[e.event_type] = counts.get(e.event_type, 0) + 1
    breakdown = ", ".join(f"{count} {etype.lower()}" for etype, count in counts.items())
    first, last = events[0], events[-1]
    return {
        "answer": (
            f"{case_id} has {len(events)} recorded timeline events ({breakdown}), "
            f"spanning {first.timestamp.date().isoformat()} to {last.timestamp.date().isoformat()}. "
            f"Earliest: '{first.title}'. Most recent: '{last.title}'."
        ),
        "supporting": [e.id for e in events],
    }


def answer_question(db: Session, question: str) -> dict:
    q = question.strip()
    ql = q.lower()
    case_ids = [m.upper() for m in CASE_ID_RE.findall(q)]
    entity_ids = [m.upper() for m in ENTITY_ID_RE.findall(q)]

    if len(case_ids) >= 2 and ("between" in ql or "connection" in ql):
        result = _answer_case_to_case(db, case_ids[0], case_ids[1])
    elif "timeline" in ql or "summarize" in ql or "summary" in ql:
        if case_ids:
            result = _answer_case_timeline_summary(db, case_ids[0])
        else:
            result = {"answer": "Please specify a case id (e.g. CASE-1001) to summarize its timeline.", "supporting": []}
    elif "why" in ql and ("flag" in ql or "alert" in ql):
        if entity_ids:
            result = _answer_why_flagged(db, entity_ids[0])
        else:
            result = {"answer": "Please specify an entity id (e.g. PERSON-101) to explain why it was flagged.", "supporting": []}
    elif "multiple cases" in ql or ("appear" in ql and "case" in ql):
        result = _answer_multi_case_entities(db)
    elif "strongest" in ql or "strongest connection" in ql:
        if entity_ids:
            result = _answer_strongest_connections(db, entity_ids[0])
        else:
            result = {"answer": "Please specify an entity id (e.g. PERSON-101) to look up its strongest connections.", "supporting": []}
    elif case_ids and ("connected" in ql or "entities" in ql):
        result = _answer_case_entities(db, case_ids[0])
    elif case_ids:
        case = db.get(Case, case_ids[0])
        if not case:
            result = {"answer": NO_DATA_MESSAGE, "supporting": []}
        else:
            result = {"answer": f"{case.id}: {case.title} -- {case.status}, {case.priority} priority, risk level {case.risk_level}. {case.description}", "supporting": [case.id]}
    elif entity_ids:
        result = _answer_strongest_connections(db, entity_ids[0])
    else:
        result = {"answer": NO_DATA_MESSAGE, "supporting": []}

    result["question"] = q
    result["disclaimer"] = "AI-assisted analytical output, generated only from the local dataset. Requires investigator verification."
    return result
