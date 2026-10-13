import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, asc
from app.config import settings
from app.models.entities import AuditLog, utc_now


def canonical_json(data: Dict[str, Any]) -> str:
    """Serializes a dictionary deterministically to maintain consistent hashes."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def compute_entry_hash(
    previous_hash: str,
    actor_id: str,
    action: str,
    metadata_json: str,
    timestamp_iso: str
) -> str:
    """Computes SHA-256 hash for an audit log entry block."""
    raw = f"{previous_hash}|{actor_id}|{action}|{metadata_json}|{timestamp_iso}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def record_audit_event(
    db: AsyncSession,
    organization_id: str,
    actor_id: str,
    action: str,
    metadata: Dict[str, Any]
) -> AuditLog:
    """
    Appends a new audit record to the hash-chained audit ledger.
    Guarantees immutable link to the latest entry in the organization.
    """
    # Fetch latest audit log entry for this organization to get previous hash
    query = (
        select(AuditLog)
        .where(AuditLog.organization_id == organization_id)
        .order_by(desc(AuditLog.timestamp), desc(AuditLog.id))
        .limit(1)
    )
    result = await db.execute(query)
    latest_entry = result.scalar_one_or_none()

    previous_hash = latest_entry.entry_hash if latest_entry else settings.AUDIT_GENESIS_PREV_HASH
    now = utc_now()
    now_iso = now.isoformat()
    meta_json_str = canonical_json(metadata)

    entry_hash = compute_entry_hash(
        previous_hash=previous_hash,
        actor_id=actor_id,
        action=action,
        metadata_json=meta_json_str,
        timestamp_iso=now_iso
    )

    log_entry = AuditLog(
        organization_id=organization_id,
        actor_id=actor_id,
        action=action,
        metadata_redacted=metadata,
        previous_hash=previous_hash,
        entry_hash=entry_hash,
        timestamp=now
    )
    db.add(log_entry)
    await db.commit()
    await db.refresh(log_entry)
    return log_entry


async def verify_audit_chain(
    db: AsyncSession,
    organization_id: str
) -> Dict[str, Any]:
    """
    Cryptographically verifies the entire audit hash chain for an organization.
    Detects any record modifications, omissions, or tampering.
    """
    query = (
        select(AuditLog)
        .where(AuditLog.organization_id == organization_id)
        .order_by(asc(AuditLog.timestamp), asc(AuditLog.id))
    )
    result = await db.execute(query)
    entries: List[AuditLog] = list(result.scalars().all())

    if not entries:
        return {
            "status": "VALID",
            "is_valid": True,
            "total_records": 0,
            "message": "Audit ledger is empty. Genesis state intact.",
            "tampered_records": [],
            "chain_head": settings.AUDIT_GENESIS_PREV_HASH
        }

    tampered_records = []
    expected_prev_hash = settings.AUDIT_GENESIS_PREV_HASH

    for idx, entry in enumerate(entries):
        # 1. Verify previous hash pointer
        if entry.previous_hash != expected_prev_hash:
            tampered_records.append({
                "record_id": entry.id,
                "index": idx,
                "issue": "PREVIOUS_HASH_MISMATCH",
                "recorded_prev_hash": entry.previous_hash,
                "expected_prev_hash": expected_prev_hash
            })

        # 2. Recompute entry hash
        meta_json_str = canonical_json(entry.metadata_redacted or {})
        recomputed = compute_entry_hash(
            previous_hash=entry.previous_hash,
            actor_id=entry.actor_id,
            action=entry.action,
            metadata_json=meta_json_str,
            timestamp_iso=entry.timestamp.isoformat()
        )

        if recomputed != entry.entry_hash:
            tampered_records.append({
                "record_id": entry.id,
                "index": idx,
                "issue": "ENTRY_HASH_CORRUPTED",
                "recorded_hash": entry.entry_hash,
                "recomputed_hash": recomputed
            })

        expected_prev_hash = entry.entry_hash

    is_valid = len(tampered_records) == 0

    return {
        "status": "VALID" if is_valid else "TAMPERED",
        "is_valid": is_valid,
        "total_records": len(entries),
        "tampered_records": tampered_records,
        "genesis_hash": settings.AUDIT_GENESIS_PREV_HASH,
        "chain_head": entries[-1].entry_hash if entries else settings.AUDIT_GENESIS_PREV_HASH,
        "first_timestamp": entries[0].timestamp.isoformat() if entries else None,
        "last_timestamp": entries[-1].timestamp.isoformat() if entries else None,
        "message": "All audit blocks cryptographically verified against hash-chain." if is_valid else "Audit ledger tampering detected!"
    }
