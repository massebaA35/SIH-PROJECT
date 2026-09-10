from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.analytics.time_machine import analyze_period, get_date_bounds
from app.database import get_db
from app.models.case import Case
from app.models.user import User
from app.security.rbac import get_current_user

router = APIRouter(prefix="/api/network-time-machine", tags=["network-time-machine"])


@router.get("/bounds")
def bounds(case_id: str | None = None, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    """The earliest/latest relationship dates available, so the frontend can
    size its date-range slider to data that actually exists."""
    if case_id and not db.get(Case, case_id):
        raise HTTPException(404, "Case not found")
    return get_date_bounds(db, case_id)


@router.get("")
def time_machine(
    start_date: date = Query(...),
    end_date: date = Query(...),
    case_id: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    if case_id and not db.get(Case, case_id):
        raise HTTPException(404, "Case not found")
    if end_date < start_date:
        raise HTTPException(400, "end_date must not be before start_date")
    return analyze_period(db, start_date, end_date, case_id)
