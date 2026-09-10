"""FastAPI dependencies for authentication and role-based access control."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.security.auth import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

ROLES = ("ADMINISTRATOR", "INVESTIGATOR", "ANALYST")


def get_current_user(token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_error
    payload = decode_access_token(token)
    if not payload:
        raise credentials_error
    user = db.get(User, payload.get("sub"))
    if not user or not user.is_active:
        raise credentials_error
    return user


def require_roles(*allowed_roles: str):
    """Dependency factory: require_roles('ADMINISTRATOR', 'INVESTIGATOR')."""

    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' is not permitted to perform this action.",
            )
        return user

    return dependency


# Any authenticated user (all three roles) may read investigative data.
require_authenticated = require_roles(*ROLES)
# Only administrators and investigators may write/modify investigative data.
require_investigator = require_roles("ADMINISTRATOR", "INVESTIGATOR")
# Only administrators may manage users / see full audit administration actions.
require_administrator = require_roles("ADMINISTRATOR")
