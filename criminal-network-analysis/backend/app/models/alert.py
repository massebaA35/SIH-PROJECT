from datetime import datetime

from sqlalchemy import String, DateTime, Text, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

SEVERITIES = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
STATUSES = ("NEW", "UNDER_REVIEW", "VERIFIED", "DISMISSED")
FINDING_LABELS = ("Potential connection", "Risk indicator", "Analytical lead", "Requires investigator verification")


class Alert(Base):
    """A rule-based suspicious-pattern detection result.

    This is an investigative decision-support tool: an alert is never a
    determination of guilt. Every alert carries a `label` drawn from
    FINDING_LABELS and must be reviewed by a human investigator before any
    action is taken.
    """

    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    case_id: Mapped[str] = mapped_column(String(20), index=True, default="")
    entity_id: Mapped[str] = mapped_column(String(20), index=True)
    severity: Mapped[str] = mapped_column(String(16))
    detection_rule: Mapped[str] = mapped_column(String(64))
    label: Mapped[str] = mapped_column(String(64), default="Requires investigator verification")
    title: Mapped[str] = mapped_column(String(255))
    evidence: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.7)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    status: Mapped[str] = mapped_column(String(32), default="NEW")
    assigned_to: Mapped[str] = mapped_column(String(128), default="")
    notes: Mapped[list] = mapped_column(JSON, default=list)  # [{author, text, at}]
