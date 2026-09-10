from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.requests import ReportRequest
from app.security.audit_chain import record_event
from app.security.rbac import get_current_user
from app.services.report_service import build_report, render_pdf

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("")
def generate_report(payload: ReportRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    report = build_report(db, payload.case_id, payload.investigator_notes)
    if not report:
        raise HTTPException(404, "Case not found")

    record_event(db, "REPORT_GENERATED", {"case_id": payload.case_id, "format": payload.format},
                 user_id=user.id, username=user.username)

    if payload.format == "pdf":
        pdf_bytes = render_pdf(report)
        return Response(
            content=pdf_bytes, media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{payload.case_id}-report.pdf"'},
        )
    return report
