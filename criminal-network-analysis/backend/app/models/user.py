from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    """Authenticated platform user. Roles: ADMINISTRATOR, INVESTIGATOR, ANALYST."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(128))
    email: Mapped[str] = mapped_column(String(128))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32))  # ADMINISTRATOR | INVESTIGATOR | ANALYST
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
