"""
Entity resolution: surface *possible* duplicate PERSON entities for a human
to confirm. Nothing here merges records automatically -- see brief section 11.

Uses difflib's SequenceMatcher (Python standard library) rather than a
heavyweight embedding model, consistent with running fully offline. It is
also fully explainable: every score is a direct string/attribute comparison
an investigator can re-derive by hand, broken into the four indicators the
Entity Resolution Assistant UI displays as separate bars: name similarity,
phone overlap, location overlap, and organization overlap.
"""
from difflib import SequenceMatcher

from sqlalchemy.orm import Session

from app.models.entities import Person
from app.models.relationship import Relationship

NAME_MATCH_THRESHOLD = 0.55
CONFIDENCE_THRESHOLD = 0.40

# Weight each indicator contributes to the overall confidence score. Name
# similarity carries the most weight since it's the primary human-readable
# signal; shared phone/location/organization are corroborating evidence.
WEIGHTS = {"name": 0.40, "phone": 0.25, "location": 0.15, "organization": 0.20}


def _name_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _overlap_score(shared_count: int, cap: int = 2) -> float:
    """Scale a shared-attribute count to 0-1, saturating at `cap` shared
    items (a 3rd shared phone number isn't meaningfully stronger evidence
    than a 2nd)."""
    return round(min(1.0, shared_count / cap), 2)


def find_possible_duplicate_persons(db: Session) -> list[dict]:
    persons = db.query(Person).all()
    edges = db.query(Relationship).all()

    # entity -> {linked entity ids}, split out by type prefix so we can tell
    # "shares a phone" apart from "shares an organization" apart from
    # "shares a location".
    linked_by_type: dict[str, dict[str, set[str]]] = {}
    for edge in edges:
        for owner, other in ((edge.source_id, edge.target_id), (edge.target_id, edge.source_id)):
            other_type = other.split("-")[0]
            linked_by_type.setdefault(owner, {}).setdefault(other_type, set()).add(other)

    candidates = []
    for i, person_a in enumerate(persons):
        for person_b in persons[i + 1:]:
            name_score = _name_similarity(person_a.name, person_b.name)
            links_a = linked_by_type.get(person_a.id, {})
            links_b = linked_by_type.get(person_b.id, {})

            shared_phones = links_a.get("PHONE", set()) & links_b.get("PHONE", set())
            shared_locations = links_a.get("LOC", set()) & links_b.get("LOC", set())
            shared_orgs = links_a.get("ORG", set()) & links_b.get("ORG", set())

            if name_score < NAME_MATCH_THRESHOLD and not (shared_phones or shared_locations or shared_orgs):
                continue

            indicators = {
                "name_similarity": round(name_score, 2),
                "phone_overlap": _overlap_score(len(shared_phones), cap=1),
                "location_overlap": _overlap_score(len(shared_locations)),
                "organization_overlap": _overlap_score(len(shared_orgs), cap=1),
            }
            confidence = round(
                indicators["name_similarity"] * WEIGHTS["name"]
                + indicators["phone_overlap"] * WEIGHTS["phone"]
                + indicators["location_overlap"] * WEIGHTS["location"]
                + indicators["organization_overlap"] * WEIGHTS["organization"],
                2,
            )
            if confidence < CONFIDENCE_THRESHOLD:
                continue

            attributes = []
            if indicators["name_similarity"] >= NAME_MATCH_THRESHOLD:
                attributes.append(f"Similar name ({round(name_score * 100)}% string similarity)")
            if shared_phones:
                attributes.append(f"{len(shared_phones)} shared phone identifier{'s' if len(shared_phones) != 1 else ''}")
            if shared_locations:
                attributes.append(f"{len(shared_locations)} shared location{'s' if len(shared_locations) != 1 else ''}")
            if shared_orgs:
                attributes.append(f"{len(shared_orgs)} shared organization{'s' if len(shared_orgs) != 1 else ''}")

            candidates.append({
                "entity_a": {"id": person_a.id, "name": person_a.name},
                "entity_b": {"id": person_b.id, "name": person_b.name},
                "confidence": confidence,
                "indicators": indicators,
                "possible_matching_attributes": attributes,
                "label": "Potential connection",
                "recommendation": "Requires investigator verification before merging or linking these records.",
            })

    candidates.sort(key=lambda c: c["confidence"], reverse=True)
    return candidates[:25]
