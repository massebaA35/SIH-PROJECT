from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai.ai_assistant import answer_question
from app.database import get_db
from app.models.user import User
from app.schemas.requests import AssistantQueryRequest
from app.security.rbac import get_current_user

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


@router.post("/ask")
def ask(payload: AssistantQueryRequest, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return answer_question(db, payload.question)
