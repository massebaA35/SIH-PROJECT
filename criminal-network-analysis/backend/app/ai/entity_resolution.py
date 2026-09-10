"""
Entity resolution: surface *possible* duplicate entities for a human to
confirm. Nothing here merges records automatically -- see brief section 11.

Uses difflib's SequenceMatcher (Python standard library) rather than a
heavyweight embedding model, consistent with running fully offline. It is
also fully explainable: every score is a direct string/attribute
comparison an investigator can re-derive by hand.
"""
from difflib import SequenceMatcher

from sqlalchemy.orm import Session

from app.models.entities import Person
from app.models.relationship import Relationship

NAME_MATCH_THRESHOLD = 0.55


def _name_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def find_possible_duplicate_persons(db: Session) -> list[dict]:
    persons = db.query(Person).all()
    edges = db.query(Relationship).all()

    # entity -> set of directly linked entity ids, used to detect "same phone / same org"
    linked: dict[str, set[str]] = {}
    for edge in edges:
        linked.setdefault(edge.source_id, set()).add(edge.target_id)
        linked.setdefault(edge.target_id, set()).add(edge.source_id)

    candidates = []
    for i, person_a in enumerate(persons):
        for person_b in persons[i + 1:]:
            name_score = _name_similarity(person_a.name, person_b.name)
            shared_links = linked.get(person_a.id, set()) & linked.get(person_b.id, set())

            if name_score < NAME_MATCH_THRESHOLD and not shared_links:
                continue

            attributes = []
            if name_score >= NAME_MATCH_THRESHOLD:
                attributes.append(f"Similar name ({round(name_score * 100)}% string similarity)")
            if shared_links:
                attributes.append(f"{len(shared_links)} shared linked entit{'y' if len(shared_links)==1 else 'ies'} (e.g. same phone/organization)")

            confidence = round(min(0.97, name_score * 0.7 + min(len(shared_links), 3) * 0.12), 2)
            if confidence < 0.4:
                continue

            candidates.append({
                "entity_a": {"id": person_a.id, "name": person_a.name},
                "entity_b": {"id": person_b.id, "name": person_b.name},
                "confidence": confidence,
                "possible_matching_attributes": attributes,
                "label": "Potential connection",
                "recommendation": "Requires investigator verification before merging or linking these records.",
            })

    candidates.sort(key=lambda c: c["confidence"], reverse=True)
    return candidates[:25]
