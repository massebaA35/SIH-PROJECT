from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserOut
from app.security.auth import create_access_token, verify_password
from app.security.audit_chain import record_event
from app.security.rbac import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not user.is_active or not verify_password(payload.password, user.hashed_password):
        record_event(db, "LOGIN_FAILED", {"username": payload.username}, username=payload.username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    token = create_access_token(subject=user.id, role=user.role)
    record_event(db, "LOGIN", {"username": user.username, "role": user.role}, user_id=user.id, username=user.username)

    return TokenResponse(
        access_token=token,
        user=UserOut(id=user.id, username=user.username, full_name=user.full_name, email=user.email, role=user.role),
    )


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return UserOut(id=user.id, username=user.username, full_name=user.full_name, email=user.email, role=user.role)


@router.post("/logout")
def logout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # JWTs are stateless in this prototype, so "logout" is enforced client-side by
    # discarding the token; we still record the event for the audit trail.
    record_event(db, "LOGOUT", {"username": user.username}, user_id=user.id, username=user.username)
    return {"status": "logged out"}
