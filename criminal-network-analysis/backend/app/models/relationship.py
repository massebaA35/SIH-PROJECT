from datetime import date

from sqlalchemy import String, Date, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

RELATION_TYPES = (
    "KNOWS", "CALLED", "MET", "WORKED_WITH", "ASSOCIATED_WITH", "TRAVELLED_TO",
    "USED", "TRANSFERRED_TO", "LINKED_TO_CASE", "ATTENDED", "COMMUNICATED_WITH",
)


class Relationship(Base):
    """An edge in the criminal network graph, linking two entities (or an
    entity and a case)."""

    __tablename__ = "relationships"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(20), index=True)
    source_type: Mapped[str] = mapped_column(String(32))
    target_id: Mapped[str] = mapped_column(String(20), index=True)
    target_type: Mapped[str] = mapped_column(String(32))
    relation_type: Mapped[str] = mapped_column(String(32))
    case_id: Mapped[str] = mapped_column(String(20), index=True, default="")
    occurred_on: Mapped[date] = mapped_column(Date)
    frequency: Mapped[int] = mapped_column(Integer, default=1)
    evidence: Mapped[str] = mapped_column(String(500), default="")
    source: Mapped[str] = mapped_column(String(64), default="Synthetic demo dataset")
    confidence: Mapped[float] = mapped_column(Float, default=0.75)
