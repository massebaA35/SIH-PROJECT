from datetime import date, datetime, timezone

from sqlalchemy import String, Date, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # e.g. CASE-1001
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(64))  # crime category
    status: Mapped[str] = mapped_column(String(32), default="Active")  # Active | Under review | Closed
    priority: Mapped[str] = mapped_column(String(16), default="normal")  # low | normal | high
    risk_level: Mapped[str] = mapped_column(String(16), default="Medium")
    region: Mapped[str] = mapped_column(String(64), default="")
    assigned_investigator: Mapped[str] = mapped_column(String(128), default="Unassigned")
    opened_date: Mapped[date] = mapped_column(Date)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
