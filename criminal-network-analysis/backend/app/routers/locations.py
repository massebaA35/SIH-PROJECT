from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.entities import Location
from app.models.event import Event
from app.models.relationship import Relationship
from app.models.user import User
from app.security.rbac import get_current_user

router = APIRouter(prefix="/api/locations", tags=["locations"])


@router.get("")
def locations(
    q: str = "",
    case_id: str | None = None,
    entity_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    records = db.query(Location).all()
    if q:
        records = [r for r in records if q.lower() in r.name.lower() or q.lower() in r.region.lower()]

    rel_q = db.query(Relationship).filter(Relationship.target_type == "LOCATION")
    if case_id:
        rel_q = rel_q.filter(Relationship.case_id == case_id)
    if date_from:
        rel_q = rel_q.filter(Relationship.occurred_on >= date_from)
    if date_to:
        rel_q = rel_q.filter(Relationship.occurred_on <= date_to)
    if entity_id:
        rel_q = rel_q.filter(Relationship.source_id == entity_id)
    location_activity: dict[str, int] = {}
    for r in rel_q.all():
        location_activity[r.target_id] = location_activity.get(r.target_id, 0) + 1

    event_q = db.query(Event).filter(Event.location_id != "")
    if case_id:
        event_q = event_q.filter(Event.case_id == case_id)
    for e in event_q.all():
        location_activity[e.location_id] = location_activity.get(e.location_id, 0) + 1

    result = []
    for loc in records:
        activity = location_activity.get(loc.id, 0)
        if (case_id or entity_id or date_from or date_to) and activity == 0:
            continue
        result.append({
            "id": loc.id, "name": loc.name, "region": loc.region, "type": loc.location_type,
            "latitude": loc.latitude, "longitude": loc.longitude, "activity_count": activity,
        })
    result.sort(key=lambda r: r["activity_count"], reverse=True)
    return {"items": result, "total": len(result)}
