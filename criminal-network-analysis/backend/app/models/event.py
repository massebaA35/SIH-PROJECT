from datetime import datetime

from sqlalchemy import String, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

EVENT_TYPES = ("CALL", "MEETING", "TRANSACTION", "TRAVEL", "CASE_EVENT", "EVIDENCE_EVENT")


class Event(Base):
    """A single point on the investigation timeline."""

    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    case_id: Mapped[str] = mapped_column(String(20), index=True)
    event_type: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    location_id: Mapped[str] = mapped_column(String(20), default="")
    related_entities: Mapped[list] = mapped_column(JSON, default=list)  # list of entity ids
    source: Mapped[str] = mapped_column(String(64), default="Synthetic demo dataset")
