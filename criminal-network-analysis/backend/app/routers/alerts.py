import itertools
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.analytics.anomaly_detection import run_all_rules
from app.database import get_db
from app.models.alert import Alert
from app.models.user import User
from app.schemas.requests import AlertUpdateRequest
from app.security.audit_chain import record_event
from app.security.rbac import get_current_user, require_investigator

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def _alert_out(a: Alert) -> dict:
    return {
        "id": a.id, "case_id": a.case_id, "entity_id": a.entity_id, "severity": a.severity,
        "detection_rule": a.detection_rule, "label": a.label, "title": a.title, "evidence": a.evidence,
        "confidence": a.confidence, "timestamp": a.timestamp.isoformat(), "status": a.status,
        "assigned_to": a.assigned_to, "notes": a.notes or [],
    }


@router.get("")
def list_alerts(
    severity: str | None = None,
    entity_id: str | None = None,
    case_id: str | None = None,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    q = db.query(Alert)
    if severity:
        q = q.filter(Alert.severity == severity)
    if entity_id:
        q = q.filter(Alert.entity_id == entity_id)
    if case_id:
        q = q.filter(Alert.case_id == case_id)
    if status:
        q = q.filter(Alert.status == status)
    if date_from:
        q = q.filter(Alert.timestamp >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        q = q.filter(Alert.timestamp <= datetime.combine(date_to, datetime.max.time()))
    alerts = q.order_by(Alert.timestamp.desc()).all()
    return {"items": [_alert_out(a) for a in alerts], "total": len(alerts)}


@router.patch("/{alert_id}")
def update_alert(alert_id: str, payload: AlertUpdateRequest, db: Session = Depends(get_db),
                  user: User = Depends(require_investigator)):
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(404, "Alert not found")

    changes = {}
    if payload.status:
        changes["status"] = (alert.status, payload.status)
        alert.status = payload.status
    if payload.assigned_to is not None:
        changes["assigned_to"] = (alert.assigned_to, payload.assigned_to)
        alert.assigned_to = payload.assigned_to
    if payload.note:
        notes = list(alert.notes or [])
        notes.append({"author": user.full_name, "text": payload.note, "at": datetime.now(timezone.utc).isoformat()})
        alert.notes = notes

    db.add(alert)
    db.commit()
    db.refresh(alert)
    record_event(db, "ALERT_UPDATED", {"alert_id": alert_id, "changes": changes, "note_added": bool(payload.note)},
                 user_id=user.id, username=user.username)
    return _alert_out(alert)


@router.post("/run-detection")
def run_detection(db: Session = Depends(get_db), user: User = Depends(require_investigator)):
    """Re-run the rule-based detectors. Alerts still awaiting review (status
    NEW) are cleared and replaced; alerts already reviewed are preserved."""
    db.query(Alert).filter(Alert.status == "NEW").delete()
    db.commit()

    existing_ids = {row[0] for row in db.query(Alert.id).all()}
    counter = itertools.count(len(existing_ids) + 1)
    drafts = run_all_rules(db)
    created = 0
    for draft in drafts:
        alert_id = f"ALERT-{next(counter):04d}"
        while alert_id in existing_ids:
            alert_id = f"ALERT-{next(counter):04d}"
        existing_ids.add(alert_id)
        db.add(Alert(id=alert_id, timestamp=datetime.now(timezone.utc), **draft))
        created += 1
    db.commit()
    record_event(db, "DETECTION_RUN", {"alerts_created": created}, user_id=user.id, username=user.username)
    return {"status": "complete", "alerts_created": created}
