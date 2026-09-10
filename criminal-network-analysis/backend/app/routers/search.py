from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.requests import SearchRequest
from app.security.rbac import get_current_user
from app.services.search_service import global_search

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("")
def search(payload: SearchRequest, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return {"query": payload.query, "results": global_search(db, payload.query, payload.types)}
