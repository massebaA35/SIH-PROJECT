from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.analytics.cross_case import compare_cases, find_related_cases
from app.database import get_db
from app.models.case import Case
from app.models.user import User
from app.schemas.requests import CrossCaseCompareRequest
from app.security.rbac import get_current_user

router = APIRouter(prefix="/api/cross-case", tags=["cross-case"])


@router.get("")
def related_cases(case_id: str = Query(...), db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    """'Find related cases' -- automatically searches every other case for
    entity/temporal overlap with the given case."""
    if not db.get(Case, case_id):
        raise HTTPException(404, "Case not found")
    all_case_ids = [c.id for c in db.query(Case.id).all()]
    matches = find_related_cases(db, case_id, all_case_ids)
    return {"case_id": case_id, "matches": matches}


@router.post("/compare")
def compare(payload: CrossCaseCompareRequest, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    if not db.get(Case, payload.case_id_a):
        raise HTTPException(404, f"Case not found: {payload.case_id_a}")
    if not db.get(Case, payload.case_id_b):
        raise HTTPException(404, f"Case not found: {payload.case_id_b}")
    if payload.case_id_a == payload.case_id_b:
        raise HTTPException(400, "Select two different cases to compare.")
    return compare_cases(db, payload.case_id_a, payload.case_id_b)
