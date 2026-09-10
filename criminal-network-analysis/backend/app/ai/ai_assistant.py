"""
Investigator-facing AI assistant ("Investigation Copilot").

This assistant answers ONLY from the local synthetic dataset -- there is no
external LLM call, so nothing here can hallucinate facts not present in the
database. Intent is matched with simple, transparent keyword/regex rules (no
black-box model). Every response is structured into the five parts an
investigator needs to act on it responsibly:

    answer            -- the direct response, in plain language
    reasoning          -- the specific facts that led to that answer
    related_entities  -- entity ids/labels referenced, each a clickable lead
    related_cases     -- case ids referenced
    source_records    -- the underlying relationship/event/alert ids an
                         investigator can pull up to verify the answer

`supporting` is kept as a flat list of ids alongside the richer fields for
backward compatibility with earlier callers.
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


def _result(
    db: Session, answer: str, *, entity_ids: list[str] | None = None, case_ids: list[str] | None = None,
    reasoning: list[str] | None = None, source_records: list[dict] | None = None, interpretation: str = "",
) -> dict:
    entity_ids = entity_ids or []
    return {
        "answer": answer,
        "reasoning": reasoning or [],
        "related_entities": [{"id": eid, "label": _entity_display_name(db, eid)} for eid in entity_ids],
        "related_cases": case_ids or [],
        "source_records": source_records or [],
        "interpretation": interpretation,
        "supporting": [r["id"] for r in (source_records or [])] or list(entity_ids),
    }


def _no_data() -> dict:
    return {
        "answer": NO_DATA_MESSAGE, "reasoning": [], "related_entities": [], "related_cases": [],
        "source_records": [], "interpretation": "", "supporting": [],
    }


def _answer_case_entities(db: Session, case_id: str) -> dict:
    edges = db.query(Relationship).filter(Relationship.case_id == case_id).all()
    if not edges:
        return _no_data()
    entities = sorted({e.source_id for e in edges} | {e.target_id for e in edges})
    named = [f"{eid} ({_entity_display_name(db, eid)})" for eid in entities]
    return _result(
        db, f"{len(entities)} entities are connected to {case_id}.",
        entity_ids=entities, case_ids=[case_id],
        reasoning=[f"{len(edges)} recorded relationships in {case_id} reference these entities.", f"Entities: {', '.join(named)}."],
        source_records=[{"id": e.id, "type": "relationship", "description": f"{e.source_id} {e.relation_type} {e.target_id}"} for e in edges],
    )


def _answer_strongest_connections(db: Session, entity_id: str) -> dict:
    edges = db.query(Relationship).filter(
        (Relationship.source_id == entity_id) | (Relationship.target_id == entity_id)
    ).all()
    if not edges:
        return _no_data()
    ranked = sorted(edges, key=lambda e: e.frequency * e.confidence, reverse=True)[:5]
    others = [e.target_id if e.source_id == entity_id else e.source_id for e in ranked]
    reasoning = [
        f"{(e.target_id if e.source_id==entity_id else e.source_id)} via {e.relation_type}, frequency {e.frequency}, confidence {round(e.confidence*100)}%"
        for e in ranked
    ]
    case_ids = sorted({e.case_id for e in ranked if e.case_id})
    return _result(
        db, f"The strongest recorded connections of {entity_id} ({_entity_display_name(db, entity_id)}) are shown below.",
        entity_ids=[entity_id, *others], case_ids=case_ids, reasoning=reasoning,
        source_records=[{"id": e.id, "type": "relationship", "description": e.evidence or e.relation_type} for e in ranked],
        interpretation="High connectivity detected. Investigator verification recommended.",
    )


def _answer_multi_case_entities(db: Session) -> dict:
    edges = db.query(Relationship).filter(Relationship.case_id != "").all()
    per_entity: dict[str, set[str]] = {}
    for e in edges:
        per_entity.setdefault(e.source_id, set()).add(e.case_id)
        per_entity.setdefault(e.target_id, set()).add(e.case_id)
    multi = {eid: cases for eid, cases in per_entity.items() if len(cases) > 1}
    if not multi:
        return _no_data()
    all_cases = sorted({c for cases in multi.values() for c in cases})
    reasoning = [f"{eid} ({_entity_display_name(db, eid)}) appears in: {', '.join(sorted(cases))}" for eid, cases in multi.items()]
    return _result(
        db, f"{len(multi)} entities appear in more than one case.",
        entity_ids=list(multi.keys()), case_ids=all_cases, reasoning=reasoning,
        interpretation="These are potential connections between cases and require investigator verification.",
    )


def _answer_why_flagged(db: Session, entity_id: str) -> dict:
    alerts = db.query(Alert).filter(Alert.entity_id == entity_id).all()
    if not alerts:
        return _no_data()
    reasoning = [f"[{a.severity}] {a.label}: {a.title} -- {a.evidence}" for a in alerts]
    case_ids = sorted({a.case_id for a in alerts if a.case_id})
    return _result(
        db, f"{entity_id} ({_entity_display_name(db, entity_id)}) has {len(alerts)} recorded alert(s).",
        entity_ids=[entity_id], case_ids=case_ids, reasoning=reasoning,
        source_records=[{"id": a.id, "type": "alert", "description": a.title} for a in alerts],
        interpretation="Alerts are explainable pattern detections, not confirmation of wrongdoing.",
    )


def _answer_explain_alert(db: Session, alert_id: str) -> dict:
    alert = db.get(Alert, alert_id.upper())
    if not alert:
        return _no_data()
    return _result(
        db, f"{alert.id}: {alert.title} ({alert.severity} severity, {alert.label}).",
        entity_ids=[alert.entity_id] if alert.entity_id else [], case_ids=[alert.case_id] if alert.case_id else [],
        reasoning=[alert.evidence, f"Detection rule: {alert.detection_rule}" if getattr(alert, "detection_rule", "") else ""],
        source_records=[{"id": alert.id, "type": "alert", "description": alert.title}],
        interpretation="This alert is an explainable pattern detection and does not establish criminal activity.",
    )


def _answer_case_to_case(db: Session, case_a: str, case_b: str) -> dict:
    edges_a = db.query(Relationship).filter(Relationship.case_id == case_a).all()
    edges_b = db.query(Relationship).filter(Relationship.case_id == case_b).all()
    entities_a = {e.source_id for e in edges_a} | {e.target_id for e in edges_a}
    entities_b = {e.source_id for e in edges_b} | {e.target_id for e in edges_b}
    shared = sorted(entities_a & entities_b)
    if not shared:
        return _result(db, f"No shared entities were found between {case_a} and {case_b} in the available dataset.", case_ids=[case_a, case_b])
    named = [f"{eid} ({_entity_display_name(db, eid)})" for eid in shared]
    return _result(
        db, f"{case_a} and {case_b} share {len(shared)} entities.",
        entity_ids=shared, case_ids=[case_a, case_b], reasoning=[f"Shared: {', '.join(named)}."],
        interpretation="This is a potential connection between cases and requires investigator verification.",
    )


def _answer_hidden_links(db: Session, entity_a: str, entity_b: str) -> dict:
    from app.graph.graph_builder import build_full_graph
    from app.analytics.path_finder import find_paths

    graph = build_full_graph(db)
    paths = find_paths(graph, entity_a, entity_b)
    if not paths:
        return _result(db, f"No hidden link was found between {entity_a} and {entity_b} in the available dataset.", entity_ids=[entity_a, entity_b])

    best = paths[0]
    chain = " -> ".join(f"{n['label']} ({n['id']})" for n in best["nodes"])
    reasoning = [f"{e['source']} {e['relation_type']} {e['target']}" + (f" ({e['evidence']})" if e.get("evidence") else "") for e in best["edges"]]
    case_ids = best.get("related_cases", [])
    return _result(
        db, f"A {best['hop_count']}-hop path connects {entity_a} and {entity_b}: {chain}.",
        entity_ids=[n["id"] for n in best["nodes"]], case_ids=case_ids, reasoning=reasoning,
        interpretation=f"Analytical lead — requires investigator verification. Confidence: {round(best['confidence']*100)}%.",
    )


def _answer_case_timeline_summary(db: Session, case_id: str) -> dict:
    events = db.query(Event).filter(Event.case_id == case_id).order_by(Event.timestamp.asc()).all()
    if not events:
        return _no_data()
    counts: dict[str, int] = {}
    for e in events:
        counts[e.event_type] = counts.get(e.event_type, 0) + 1
    breakdown = ", ".join(f"{count} {etype.lower()}" for etype, count in counts.items())
    first, last = events[0], events[-1]
    return _result(
        db, f"{case_id} has {len(events)} recorded timeline events ({breakdown}), spanning {first.timestamp.date().isoformat()} to {last.timestamp.date().isoformat()}.",
        case_ids=[case_id],
        reasoning=[f"Earliest: '{first.title}' on {first.timestamp.date().isoformat()}.", f"Most recent: '{last.title}' on {last.timestamp.date().isoformat()}."],
        source_records=[{"id": e.id, "type": "event", "description": e.title} for e in events],
    )


def answer_question(db: Session, question: str) -> dict:
    q = question.strip()
    ql = q.lower()
    case_ids = [m.upper() for m in CASE_ID_RE.findall(q)]
    entity_ids = [m.upper() for m in ENTITY_ID_RE.findall(q)]
    alert_id_match = re.search(r"\bALERT-\d+\b", q, re.IGNORECASE)

    if "hidden link" in ql and len(entity_ids) >= 2:
        result = _answer_hidden_links(db, entity_ids[0], entity_ids[1])
    elif len(case_ids) >= 2 and ("between" in ql or "connection" in ql):
        result = _answer_case_to_case(db, case_ids[0], case_ids[1])
    elif "timeline" in ql or "summarize" in ql or "summary" in ql:
        if case_ids:
            result = _answer_case_timeline_summary(db, case_ids[0])
        else:
            result = _result(db, "Please specify a case id (e.g. CASE-1001) to summarize its timeline.")
    elif "explain" in ql and alert_id_match:
        result = _answer_explain_alert(db, alert_id_match.group(0))
    elif "why" in ql and ("flag" in ql or "alert" in ql):
        if entity_ids:
            result = _answer_why_flagged(db, entity_ids[0])
        else:
            result = _result(db, "Please specify an entity id (e.g. PERSON-101) to explain why it was flagged.")
    elif "multiple cases" in ql or ("appear" in ql and "case" in ql):
        result = _answer_multi_case_entities(db)
    elif "strongest" in ql or "strongest connection" in ql:
        if entity_ids:
            result = _answer_strongest_connections(db, entity_ids[0])
        else:
            result = _result(db, "Please specify an entity id (e.g. PERSON-101) to look up its strongest connections.")
    elif case_ids and ("connected" in ql or "entities" in ql):
        result = _answer_case_entities(db, case_ids[0])
    elif case_ids:
        case = db.get(Case, case_ids[0])
        if not case:
            result = _no_data()
        else:
            result = _result(
                db, f"{case.id}: {case.title} -- {case.status}, {case.priority} priority, risk level {case.risk_level}.",
                case_ids=[case.id], reasoning=[case.description],
            )
    elif entity_ids:
        result = _answer_strongest_connections(db, entity_ids[0])
    else:
        result = _no_data()

    result["question"] = q
    result["disclaimer"] = "AI-Assisted Analytical Output — Requires Investigator Verification. Generated only from the local dataset."
    return result
