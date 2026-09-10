from datetime import datetime

from sqlalchemy import String, DateTime, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuditLog(Base):
    """A blockchain-inspired, tamper-evident audit record.

    Each row's `current_hash` is SHA-256(previous_hash + event_data +
    timestamp). Because every record commits to the hash of the one before
    it, altering any historical row changes its hash and breaks the chain
    for every record after it -- which the /api/audit/verify endpoint
    detects. This is a lightweight hash-chain, not a distributed ledger;
    see docs/SECURITY.md for the migration path to a permissioned
    blockchain such as Hyperledger Fabric.
    """

    __tablename__ = "audit_logs"

    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(64))  # LOGIN | DATA_UPLOAD | ENTITY_MODIFIED | ...
    user_id: Mapped[str] = mapped_column(String(20), default="")
    username: Mapped[str] = mapped_column(String(64), default="")
    event_data: Mapped[str] = mapped_column(Text)  # canonical JSON string
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    previous_hash: Mapped[str] = mapped_column(String(64))
    current_hash: Mapped[str] = mapped_column(String(64), index=True)
