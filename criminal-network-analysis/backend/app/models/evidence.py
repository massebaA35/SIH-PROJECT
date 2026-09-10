from datetime import datetime

from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    case_id: Mapped[str] = mapped_column(String(20), index=True)
    entity_id: Mapped[str] = mapped_column(String(20), default="")
    evidence_type: Mapped[str] = mapped_column(String(64))  # document | call log | transaction record | statement
    description: Mapped[str] = mapped_column(Text)
    sha256_hash: Mapped[str] = mapped_column(String(64))
    source: Mapped[str] = mapped_column(String(128), default="Synthetic demo dataset")
    uploaded_by: Mapped[str] = mapped_column(String(64), default="")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime)
