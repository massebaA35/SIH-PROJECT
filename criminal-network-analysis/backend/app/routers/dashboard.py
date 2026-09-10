from collections import Counter
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.alert import Alert
from app.models.case import Case
from app.models.entities import Person, Organization, Vehicle, Phone, Location, Account
from app.models.event import Event
from app.models.relationship import Relationship
from app.models.user import User
from app.security.rbac import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(
    region: str | None = None,
    category: str | None = None,
    risk_level: str | None = None,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    cases_q = db.query(Case)
    if region:
        cases_q = cases_q.filter(Case.region == region)
    if category:
        cases_q = cases_q.filter(Case.category == category)
    if risk_level:
        cases_q = cases_q.filter(Case.risk_level == risk_level)
    if date_from:
        cases_q = cases_q.filter(Case.opened_date >= date_from)
    if date_to:
        cases_q = cases_q.filter(Case.opened_date <= date_to)
    cases = cases_q.all()
    case_ids = {c.id for c in cases}

    active_cases = sum(1 for c in cases if c.status == "Active")
    persons = db.query(Person).count()
    organizations = db.query(Organization).count()
    vehicles = db.query(Vehicle).count()
    locations = db.query(Location).count()
    phones = db.query(Phone).count()
    accounts = db.query(Account).count()
    relationships = db.query(Relationship).count()
    alerts_all = db.query(Alert).all()
    high_priority_alerts = sum(1 for a in alerts_all if a.severity in ("HIGH", "CRITICAL"))

    kpis = [
        {"label": "Total Active Cases", "value": active_cases, "delta": f"{len(cases)} total in view"},
        {"label": "Persons of Interest", "value": persons, "delta": "Synthetic dataset"},
        {"label": "Organizations", "value": organizations, "delta": ""},
        {"label": "Vehicles", "value": vehicles, "delta": ""},
        {"label": "Locations", "value": locations, "delta": ""},
        {"label": "Phone Numbers", "value": phones, "delta": ""},
        {"label": "Financial Entities", "value": accounts, "delta": ""},
        {"label": "Detected Relationships", "value": relationships, "delta": ""},
        {"label": "Suspicious Activities", "value": len(alerts_all), "delta": f"{high_priority_alerts} high priority"},
        {"label": "High-priority Alerts", "value": high_priority_alerts, "delta": "HIGH or CRITICAL severity"},
    ]

    cases_by_category = Counter(c.category for c in cases)
    cases_over_time = Counter(c.opened_date.strftime("%Y-%m") for c in cases)

    events_q = db.query(Event)
    if case_ids:
        events_q = events_q.filter(Event.case_id.in_(case_ids))
    network_activity_over_time = Counter(e.timestamp.strftime("%Y-%m") for e in events_q.all())

    entity_distribution = {
        "PERSON": persons, "ORGANIZATION": organizations, "VEHICLE": vehicles,
        "PHONE": phones, "LOCATION": locations, "ACCOUNT": accounts,
    }

    geo_activity = Counter()
    location_lookup = {loc.id: loc for loc in db.query(Location).all()}
    location_side = or_(Relationship.source_type == "LOCATION", Relationship.target_type == "LOCATION")
    rel_q = db.query(Relationship).filter(location_side) if not case_ids else \
        db.query(Relationship).filter(location_side, Relationship.case_id.in_(case_ids))
    for r in rel_q.all():
        loc_id = r.source_id if r.source_type == "LOCATION" else r.target_id
        loc = location_lookup.get(loc_id)
        if loc:
            geo_activity[loc.region] += 1

    alert_severity_distribution = Counter(a.severity for a in alerts_all)

    connection_counts = Counter()
    for r in db.query(Relationship).filter(Relationship.source_type == "PERSON").all():
        connection_counts[r.source_id] += 1
    for r in db.query(Relationship).filter(Relationship.target_type == "PERSON").all():
        connection_counts[r.target_id] += 1
    top_person_ids = [pid for pid, _ in connection_counts.most_common(6)]
    persons_by_id = {p.id: p for p in db.query(Person).filter(Person.id.in_(top_person_ids)).all()}
    top_connected = [
        {"id": pid, "label": persons_by_id[pid].name, "score": connection_counts[pid]}
        for pid in top_person_ids if pid in persons_by_id
    ]

    recent_alerts = sorted(alerts_all, key=lambda a: a.timestamp, reverse=True)[:8]

    return {
        "kpis": kpis,
        "charts": {
            "cases_by_category": dict(cases_by_category),
            "cases_over_time": dict(sorted(cases_over_time.items())),
            "network_activity_over_time": dict(sorted(network_activity_over_time.items())),
            "entity_distribution": entity_distribution,
            "geographic_activity": dict(geo_activity),
            "alert_severity_distribution": dict(alert_severity_distribution),
        },
        "alerts": [
            {"id": a.id, "severity": a.severity, "label": a.label, "title": a.title, "explanation": a.evidence,
             "entity": a.entity_id, "time": a.timestamp.isoformat(), "status": a.status}
            for a in recent_alerts
        ],
        "top_entities": top_connected,
        "filters_applied": {"region": region, "category": category, "risk_level": risk_level, "date_from": date_from, "date_to": date_to},
    }
