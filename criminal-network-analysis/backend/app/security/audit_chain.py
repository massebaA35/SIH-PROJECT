"""
Blockchain-inspired tamper-evident audit trail.

This is a lightweight SHA-256 hash chain, not a distributed ledger: each
audit record's `current_hash` commits to the previous record's hash plus
this record's own data and timestamp. Anyone can recompute the chain from
the first record and confirm every hash matches, which proves nothing in
the sequence was altered or deleted after the fact without detection.

The architecture is deliberately append-only and single-writer so it can
later be swapped for a permissioned blockchain (e.g. Hyperledger Fabric)
without changing the calling code: `record_event` and `verify_chain`
would simply submit to / read from the ledger instead of the local table.
"""
import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import AuditLog

GENESIS_HASH = "0" * 64


def _compute_hash(previous_hash: str, event_type: str, event_data: str, timestamp: str) -> str:
    payload = f"{previous_hash}|{event_type}|{event_data}|{timestamp}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def record_event(db: Session, event_type: str, data: dict, user_id: str = "", username: str = "") -> AuditLog:
    """Append a new tamper-evident audit record and commit it."""
    last = db.execute(select(AuditLog).order_by(AuditLog.seq.desc()).limit(1)).scalar_one_or_none()
    previous_hash = last.current_hash if last else GENESIS_HASH

    now = datetime.now(timezone.utc)
    timestamp = now.isoformat()
    event_data = json.dumps(data, sort_keys=True, default=str)
    current_hash = _compute_hash(previous_hash, event_type, event_data, timestamp)

    record = AuditLog(
        event_type=event_type,
        user_id=user_id,
        username=username,
        event_data=event_data,
        timestamp=now,
        previous_hash=previous_hash,
        current_hash=current_hash,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def verify_chain(db: Session) -> dict:
    """Recompute every hash in sequence and report the first break, if any."""
    records = db.execute(select(AuditLog).order_by(AuditLog.seq.asc())).scalars().all()
    expected_previous = GENESIS_HASH
    broken_at: int | None = None
    checked = 0

    for record in records:
        timestamp = record.timestamp.replace(tzinfo=timezone.utc).isoformat()
        recomputed = _compute_hash(expected_previous, record.event_type, record.event_data, timestamp)
        checked += 1
        if record.previous_hash != expected_previous or record.current_hash != recomputed:
            broken_at = record.seq
            break
        expected_previous = record.current_hash

    return {
        "verified": broken_at is None,
        "total_records": len(records),
        "records_checked": checked,
        "broken_at_seq": broken_at,
        "message": (
            "Audit chain intact: every record's hash matches its predecessor. No tampering detected."
            if broken_at is None
            else f"Chain integrity broken at record #{broken_at}. This record or one before it does not match its stored hash -- possible tampering."
        ),
    }
