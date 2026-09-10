"""
Rule-based suspicious-pattern detection (brief section G).

Every rule is a small, auditable function: the "detection_rule" string
identifies exactly which rule fired, and "evidence" explains in plain
language what was observed. No rule ever concludes guilt -- each alert
carries a `label` from the shared finding-label vocabulary and a status
that starts at NEW, awaiting investigator review.
"""
from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.entities import Person, Phone
from app.models.event import Event
from app.models.relationship import Relationship

RECENT_WINDOW_DAYS = 14
NIGHT_HOURS = set(range(0, 6))


def _pct_bucket(value: int, medium: int, high: int, critical: int) -> str:
    if value >= critical:
        return "CRITICAL"
    if value >= high:
        return "HIGH"
    if value >= medium:
        return "MEDIUM"
    return "LOW"


def _draft(entity_id: str, severity: str, rule: str, title: str, evidence: str, confidence: float,
           label: str = "Risk indicator", case_id: str = "") -> dict:
    return {
        "entity_id": entity_id,
        "severity": severity,
        "detection_rule": rule,
        "title": title,
        "evidence": evidence,
        "confidence": round(confidence, 2),
        "label": label,
        "case_id": case_id,
        "status": "NEW",
    }


def rule_unusual_communication_frequency(relationships: list[Relationship]) -> list[dict]:
    totals: dict[str, int] = defaultdict(int)
    for r in relationships:
        if r.relation_type in ("CALLED", "COMMUNICATED_WITH"):
            totals[r.source_id] += r.frequency
            totals[r.target_id] += r.frequency

    alerts = []
    for entity_id, total in totals.items():
        if total >= 12:
            alerts.append(_draft(
                entity_id, _pct_bucket(total, 12, 20, 30), "unusual_communication_frequency",
                "Unusual communication frequency",
                f"This entity is party to {total} recorded communication events, well above the typical range for this dataset.",
                min(0.95, 0.5 + total / 60), label="Risk indicator",
            ))
    return alerts


def rule_sudden_communication_increase(events: list[Event]) -> list[dict]:
    now = datetime.now()
    recent_cutoff = now - timedelta(days=RECENT_WINDOW_DAYS)
    prior_cutoff = now - timedelta(days=RECENT_WINDOW_DAYS * 2)

    recent: dict[str, int] = defaultdict(int)
    prior: dict[str, int] = defaultdict(int)
    for event in events:
        if event.event_type != "CALL":
            continue
        bucket = recent if event.timestamp >= recent_cutoff else (prior if event.timestamp >= prior_cutoff else None)
        if bucket is None:
            continue
        for entity_id in (event.related_entities or []):
            bucket[entity_id] += 1

    alerts = []
    for entity_id, recent_count in recent.items():
        prior_count = prior.get(entity_id, 0)
        if recent_count >= 3 and recent_count >= max(2, prior_count) * 2:
            alerts.append(_draft(
                entity_id, _pct_bucket(recent_count, 3, 5, 8), "sudden_communication_increase",
                "Sudden increase in communication",
                f"Recorded calls involving this entity rose from {prior_count} to {recent_count} within the last {RECENT_WINDOW_DAYS} days.",
                min(0.9, 0.5 + recent_count / 20), label="Risk indicator",
            ))
    return alerts


def rule_repeated_interactions(relationships: list[Relationship]) -> list[dict]:
    pair_freq: dict[tuple[str, str], int] = defaultdict(int)
    pair_case: dict[tuple[str, str], str] = {}
    for r in relationships:
        key = tuple(sorted((r.source_id, r.target_id)))
        pair_freq[key] += r.frequency
        pair_case[key] = r.case_id

    alerts = []
    for (a, b), freq in pair_freq.items():
        if freq >= 9:
            alerts.append(_draft(
                a, _pct_bucket(freq, 6, 10, 16), "repeated_interactions",
                "Repeated interactions between entities",
                f"{a} and {b} have {freq} recorded interactions, indicating a persistent link worth reviewing.",
                min(0.9, 0.5 + freq / 40), label="Analytical lead", case_id=pair_case.get((a, b), ""),
            ))
    return alerts


def rule_financial_anomaly(relationships: list[Relationship]) -> list[dict]:
    transfers = [r for r in relationships if r.relation_type == "TRANSFERRED_TO"]
    outgoing: dict[str, list[str]] = defaultdict(list)
    for r in transfers:
        outgoing[r.source_id].append(r.target_id)

    alerts = []

    # simple cycle check: A -> B -> ... -> A within transfer edges (circular flow)
    def find_cycle(start: str) -> list[str] | None:
        stack = [(start, [start])]
        visited_paths = 0
        while stack and visited_paths < 200:
            node, path = stack.pop()
            visited_paths += 1
            for nxt in outgoing.get(node, []):
                if nxt == start and len(path) > 2:
                    return path + [nxt]
                if nxt not in path:
                    stack.append((nxt, path + [nxt]))
        return None

    seen_cycle_entities: set[str] = set()
    for account_id in list(outgoing.keys()):
        if account_id in seen_cycle_entities:
            continue
        cycle = find_cycle(account_id)
        if cycle:
            seen_cycle_entities.update(cycle)
            case_id = next((r.case_id for r in transfers if r.source_id == account_id), "")
            alerts.append(_draft(
                account_id, "HIGH", "financial_anomaly",
                "Unusual financial transaction pattern",
                f"A circular fund flow was detected: {' -> '.join(cycle)}.",
                0.8, label="Risk indicator", case_id=case_id,
            ))

    # high fan-out from a single account
    for account_id, targets in outgoing.items():
        if len(set(targets)) >= 4:
            case_id = next((r.case_id for r in transfers if r.source_id == account_id), "")
            alerts.append(_draft(
                account_id, "MEDIUM", "financial_anomaly",
                "Unusual financial transaction pattern",
                f"This account transferred funds to {len(set(targets))} distinct accounts, more than the typical pattern in this dataset.",
                0.7, label="Risk indicator", case_id=case_id,
            ))
    return alerts


def rule_shared_vehicle_across_cases(relationships: list[Relationship]) -> list[dict]:
    vehicle_cases: dict[str, set[str]] = defaultdict(set)
    for r in relationships:
        for entity_id, entity_type in ((r.source_id, r.source_type), (r.target_id, r.target_type)):
            if entity_type == "VEHICLE" and r.case_id:
                vehicle_cases[entity_id].add(r.case_id)

    alerts = []
    for vehicle_id, cases in vehicle_cases.items():
        if len(cases) >= 2:
            alerts.append(_draft(
                vehicle_id, "MEDIUM", "shared_vehicle_across_cases",
                "Same vehicle appears across multiple cases",
                f"This vehicle is referenced in {len(cases)} distinct cases: {', '.join(sorted(cases))}.",
                0.75, label="Analytical lead", case_id=sorted(cases)[0],
            ))
    return alerts


def rule_shared_phone_multiple_entities(relationships: list[Relationship]) -> list[dict]:
    phone_persons: dict[str, set[str]] = defaultdict(set)
    for r in relationships:
        if r.source_type == "PHONE" and r.target_type == "PERSON":
            phone_persons[r.source_id].add(r.target_id)
        elif r.target_type == "PHONE" and r.source_type == "PERSON":
            phone_persons[r.target_id].add(r.source_id)

    alerts = []
    for phone_id, persons in phone_persons.items():
        if len(persons) >= 2:
            alerts.append(_draft(
                phone_id, "HIGH", "shared_phone_multiple_entities",
                "Same phone number associated with multiple entities",
                f"This phone number is linked to {len(persons)} different persons: {', '.join(sorted(persons))}.",
                0.85, label="Risk indicator",
            ))
    return alerts


def rule_repeated_location_movement(relationships: list[Relationship]) -> list[dict]:
    travel_freq: dict[tuple[str, str], int] = defaultdict(int)
    for r in relationships:
        if r.relation_type == "TRAVELLED_TO":
            key = (r.source_id, r.target_id)
            travel_freq[key] += r.frequency

    alerts = []
    for (entity_id, location_id), freq in travel_freq.items():
        if freq >= 4:
            alerts.append(_draft(
                entity_id, "MEDIUM", "repeated_location_movement",
                "Repeated movement between locations",
                f"This entity travelled to {location_id} {freq} times in the recorded data, more than the typical pattern.",
                0.7, label="Analytical lead",
            ))
    return alerts


def rule_entities_shared_across_cases(relationships: list[Relationship]) -> list[dict]:
    entity_cases: dict[str, set[str]] = defaultdict(set)
    for r in relationships:
        if not r.case_id:
            continue
        entity_cases[r.source_id].add(r.case_id)
        entity_cases[r.target_id].add(r.case_id)

    alerts = []
    for entity_id, cases in entity_cases.items():
        if len(cases) >= 5:  # > CASES_PER_COMMUNITY (4), so only entities reaching beyond their own case cluster fire
            alerts.append(_draft(
                entity_id, "HIGH", "entities_shared_across_cases",
                "Entity appears in multiple cases",
                f"This entity is connected to {len(cases)} separate cases: {', '.join(sorted(cases))}.",
                0.8, label="Analytical lead", case_id=sorted(cases)[0],
            ))
    return alerts


def rule_rapid_connectivity_change(relationships: list[Relationship]) -> list[dict]:
    cutoff = datetime.now().date() - timedelta(days=RECENT_WINDOW_DAYS)
    recent_count: dict[str, int] = defaultdict(int)
    older_count: dict[str, int] = defaultdict(int)

    for r in relationships:
        bucket = recent_count if r.occurred_on >= cutoff else older_count
        bucket[r.source_id] += 1
        bucket[r.target_id] += 1

    alerts = []
    for entity_id, recent in recent_count.items():
        baseline = older_count.get(entity_id, 0)
        if recent >= 4 and recent > baseline * 1.5:
            alerts.append(_draft(
                entity_id, "MEDIUM", "rapid_connectivity_change",
                "Rapid change in network connectivity",
                f"This entity gained {recent} new recorded connections in the last {RECENT_WINDOW_DAYS} days, compared to {baseline} before that.",
                0.65, label="Risk indicator",
            ))
    return alerts


def rule_unusual_time_window_activity(events: list[Event]) -> list[dict]:
    entity_night_events: dict[str, list[str]] = defaultdict(list)
    for event in events:
        if event.timestamp.hour in NIGHT_HOURS:
            for entity_id in (event.related_entities or []):
                entity_night_events[entity_id].append(event.id)

    alerts = []
    for entity_id, event_ids in entity_night_events.items():
        if len(event_ids) >= 2:
            alerts.append(_draft(
                entity_id, "LOW", "unusual_time_window_activity",
                "Activity outside normal time windows",
                f"This entity appears in {len(event_ids)} recorded events between midnight and 6 AM ({', '.join(event_ids)}).",
                0.55, label="Potential connection",
            ))
    return alerts


def run_all_rules(db: Session) -> list[dict]:
    relationships = db.query(Relationship).all()
    events = db.query(Event).all()

    drafts: list[dict] = []
    drafts += rule_unusual_communication_frequency(relationships)
    drafts += rule_sudden_communication_increase(events)
    drafts += rule_repeated_interactions(relationships)
    drafts += rule_financial_anomaly(relationships)
    drafts += rule_shared_vehicle_across_cases(relationships)
    drafts += rule_shared_phone_multiple_entities(relationships)
    drafts += rule_repeated_location_movement(relationships)
    drafts += rule_entities_shared_across_cases(relationships)
    drafts += rule_rapid_connectivity_change(relationships)
    drafts += rule_unusual_time_window_activity(events)
    return drafts
