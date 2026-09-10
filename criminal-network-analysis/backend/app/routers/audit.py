from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit import AuditLog
from app.models.user import User
from app.security.audit_chain import verify_chain
from app.security.rbac import require_investigator

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/logs")
def audit_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    event_type: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(require_investigator),
):
    q = db.query(AuditLog)
    if event_type:
        q = q.filter(AuditLog.event_type == event_type)
    records = q.order_by(AuditLog.seq.desc()).limit(limit).all()
    return {
        "items": [
            {
                "seq": r.seq, "event_type": r.event_type, "username": r.username,
                "timestamp": r.timestamp.isoformat(), "previous_hash": r.previous_hash,
                "current_hash": r.current_hash, "event_data": r.event_data,
            }
            for r in records
        ],
        "total": q.count(),
    }


@router.get("/verify")
def audit_verify(db: Session = Depends(get_db), _user: User = Depends(require_investigator)):
    """Recompute the SHA-256 hash chain end-to-end and report whether it is
    intact. See app/security/audit_chain.py for the explanation of why this
    is described as a 'blockchain-inspired tamper-evident audit trail'
    rather than a real distributed ledger."""
    return verify_chain(db)
