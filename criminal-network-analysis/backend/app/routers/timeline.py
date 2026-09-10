from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.event import Event
from app.models.user import User
from app.security.rbac import get_current_user

router = APIRouter(prefix="/api/timeline", tags=["timeline"])


@router.get("")
def timeline(
    case_id: str | None = None,
    entity_id: str | None = None,
    event_type: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    q = db.query(Event)
    if case_id:
        q = q.filter(Event.case_id == case_id)
    if event_type:
        q = q.filter(Event.event_type == event_type)
    if date_from:
        q = q.filter(Event.timestamp >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        q = q.filter(Event.timestamp <= datetime.combine(date_to, datetime.max.time()))

    events = q.order_by(Event.timestamp.desc()).limit(500).all()
    if entity_id:
        events = [e for e in events if entity_id in (e.related_entities or [])]

    return {
        "items": [
            {
                "id": e.id, "case_id": e.case_id, "type": e.event_type, "title": e.title,
                "description": e.description, "timestamp": e.timestamp.isoformat(),
                "location_id": e.location_id, "related_entities": e.related_entities or [],
            }
            for e in events
        ],
        "total": len(events),
    }
