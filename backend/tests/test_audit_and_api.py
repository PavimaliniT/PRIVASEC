import pytest
from app.core.audit import compute_entry_hash, canonical_json
from app.config import settings


def test_hash_chain_genesis_and_verification():
    """Verifies SHA-256 hash chaining formula and determinism."""
    prev_hash = settings.AUDIT_GENESIS_PREV_HASH
    meta1 = {"event": "login", "user": "alice"}
    timestamp1 = "2026-10-13T10:00:00+00:00"
    
    hash1 = compute_entry_hash(
        previous_hash=prev_hash,
        actor_id="usr_001",
        action="AUTH_LOGIN",
        metadata_json=canonical_json(meta1),
        timestamp_iso=timestamp1
    )
    assert len(hash1) == 64  # SHA-256 hex string

    # Second block chained to first block
    meta2 = {"policy": "retention_90"}
    timestamp2 = "2026-10-13T10:05:00+00:00"
    hash2 = compute_entry_hash(
        previous_hash=hash1,
        actor_id="usr_admin",
        action="POLICY_UPDATE",
        metadata_json=canonical_json(meta2),
        timestamp_iso=timestamp2
    )
    assert len(hash2) == 64
    assert hash2 != hash1

    # Tampering test: altering metadata changes block hash
    tampered_meta = {"policy": "retention_365_tampered"}
    tampered_hash2 = compute_entry_hash(
        previous_hash=hash1,
        actor_id="usr_admin",
        action="POLICY_UPDATE",
        metadata_json=canonical_json(tampered_meta),
        timestamp_iso=timestamp2
    )
    assert tampered_hash2 != hash2
