"""Cross-Case DNA: explainable similarity scoring between two cases based
on shared entities, shared entity types, and temporal overlap of their
recorded relationships. This is a structural comparison of the supplied
synthetic data, not an assessment of whether the cases are truly linked
in reality."""
from datetime import date

from sqlalchemy.orm import Session

from app.models.relationship import Relationship
from app.services.entity_service import entity_type_from_id, display_name, ENTITY_TABLES

TYPE_WEIGHTS = {"PERSON": 3, "ORGANIZATION": 2, "VEHICLE": 2, "PHONE": 2, "ACCOUNT": 2, "LOCATION": 1}


def _case_signature(db: Session, case_id: str) -> dict:
    edges = db.query(Relationship).filter(Relationship.case_id == case_id).all()
    entity_ids: set[str] = set()
    dates: list[date] = []
    for e in edges:
        entity_ids.add(e.source_id)
        entity_ids.add(e.target_id)
        dates.append(e.occurred_on)
    by_type: dict[str, set[str]] = {}
    for eid in entity_ids:
        etype = entity_type_from_id(eid)
        if etype:
            by_type.setdefault(etype, set()).add(eid)
    return {
        "entity_ids": entity_ids,
        "by_type": by_type,
        "date_min": min(dates) if dates else None,
        "date_max": max(dates) if dates else None,
    }


def _temporal_similarity(sig_a: dict, sig_b: dict) -> tuple[float, str]:
    if not sig_a["date_min"] or not sig_b["date_min"]:
        return 0.0, "UNKNOWN"
    latest_start = max(sig_a["date_min"], sig_b["date_min"])
    earliest_end = min(sig_a["date_max"], sig_b["date_max"])
    overlap_days = max(0, (earliest_end - latest_start).days)
    span_a = max(1, (sig_a["date_max"] - sig_a["date_min"]).days)
    span_b = max(1, (sig_b["date_max"] - sig_b["date_min"]).days)
    union_span = max(span_a, span_b, overlap_days)
    fraction = overlap_days / union_span if union_span else 0.0
    label = "HIGH" if fraction > 0.5 else "MEDIUM" if fraction > 0.15 else "LOW"
    return round(fraction, 2), label


def compare_cases(db: Session, case_id_a: str, case_id_b: str) -> dict:
    sig_a = _case_signature(db, case_id_a)
    sig_b = _case_signature(db, case_id_b)

    shared_by_type: dict[str, list[str]] = {}
    weighted_shared = 0
    for etype, ids_a in sig_a["by_type"].items():
        ids_b = sig_b["by_type"].get(etype, set())
        shared = sorted(ids_a & ids_b)
        if shared:
            shared_by_type[etype] = shared
            weighted_shared += len(shared) * TYPE_WEIGHTS.get(etype, 1)

    union_size = len(sig_a["entity_ids"] | sig_b["entity_ids"])
    max_possible_weight = union_size * max(TYPE_WEIGHTS.values()) if union_size else 1
    entity_score = min(1.0, weighted_shared / max_possible_weight) if max_possible_weight else 0.0

    temporal_fraction, temporal_label = _temporal_similarity(sig_a, sig_b)

    similarity = round(100 * (0.7 * entity_score + 0.3 * temporal_fraction))

    reasons = []
    for etype in ("PERSON", "ORGANIZATION", "VEHICLE", "PHONE", "ACCOUNT", "LOCATION"):
        count = len(shared_by_type.get(etype, []))
        if count:
            noun = etype.title() if count == 1 else etype.title() + "s"
            reasons.append(f"{count} shared {noun.lower()}")
    if temporal_label == "HIGH":
        reasons.append("substantial temporal overlap between recorded activity in both cases")
    elif temporal_label == "MEDIUM":
        reasons.append("some temporal overlap between recorded activity in both cases")

    total_shared_entities = sum(len(v) for v in shared_by_type.values())

    return {
        "case_id_a": case_id_a,
        "case_id_b": case_id_b,
        "similarity_score": similarity,
        "breakdown": {
            "shared_entities": total_shared_entities,
            "shared_persons": len(shared_by_type.get("PERSON", [])),
            "shared_organizations": len(shared_by_type.get("ORGANIZATION", [])),
            "shared_vehicles": len(shared_by_type.get("VEHICLE", [])),
            "shared_phones": len(shared_by_type.get("PHONE", [])),
            "shared_accounts": len(shared_by_type.get("ACCOUNT", [])),
            "shared_locations": len(shared_by_type.get("LOCATION", [])),
            "temporal_similarity": temporal_label,
        },
        "shared_entity_ids": {etype: [{"id": eid, "label": display_name(db.get(ENTITY_TABLES[etype], eid))} for eid in ids] for etype, ids in shared_by_type.items()},
        "explanation": (
            f"Cases {case_id_a} and {case_id_b} share {total_shared_entities} recorded entities ({', '.join(reasons)})."
            if reasons else f"No shared entities or temporal overlap were found between {case_id_a} and {case_id_b} in the available dataset."
        ),
        "label": "Analytical lead — requires investigator verification",
        "disclaimer": "This score reflects structural overlap in the supplied data only. It does not establish that the two cases are connected in reality.",
    }


def find_related_cases(db: Session, case_id: str, all_case_ids: list[str], limit: int = 5) -> list[dict]:
    results = []
    for other_id in all_case_ids:
        if other_id == case_id:
            continue
        comparison = compare_cases(db, case_id, other_id)
        if comparison["similarity_score"] > 0:
            results.append(comparison)
    results.sort(key=lambda c: c["similarity_score"], reverse=True)
    return results[:limit]
