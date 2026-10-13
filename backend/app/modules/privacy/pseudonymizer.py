import hmac
import hashlib
import secrets
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.core.security import encrypt_sensitive_field, decrypt_sensitive_field
from app.models.entities import PseudonymMapping, utc_now


def generate_deterministic_pseudonym(identifier: str, domain: str = "default", prefix: str = "usr_") -> str:
    """
    Computes a deterministic pseudonym using HMAC-SHA256 with domain separation.
    Allows consistent analytics linkage across sessions without exposing the raw identifier.
    """
    key = f"{settings.HMAC_PEPPER_KEY}:{domain}".encode("utf-8")
    raw = identifier.strip().lower().encode("utf-8")
    digest = hmac.new(key, raw, hashlib.sha256).hexdigest()
    # 16 hex chars (64-bit entropy) prefixed
    return f"{prefix}{digest[:16]}"


def generate_random_token(prefix: str = "tok_") -> str:
    """Generates a random opaque non-linkable token."""
    return f"{prefix}{secrets.token_hex(12)}"


async def create_pseudonym_mapping(
    db: AsyncSession,
    organization_id: str,
    original_identifier: str,
    purpose: str = "analytics",
    deterministic: bool = True
) -> Dict[str, Any]:
    """
    Creates a pseudonym and stores the original identifier in the access-controlled
    encrypted mapping vault.
    """
    if deterministic:
        token = generate_deterministic_pseudonym(
            original_identifier,
            domain=f"{organization_id}:{purpose}"
        )
    else:
        token = generate_random_token()

    # Check if mapping already exists for this token and organization
    query = select(PseudonymMapping).where(
        PseudonymMapping.organization_id == organization_id,
        PseudonymMapping.token == token
    )
    res = await db.execute(query)
    existing = res.scalar_one_or_none()

    if existing:
        return {
            "token": token,
            "purpose": existing.purpose,
            "created_at": existing.created_at.isoformat(),
            "key_version": existing.key_version,
            "is_new": False
        }

    # Encrypt original identifier with AES-256-GCM using organization ID as associated authenticated data
    aad = f"org:{organization_id}".encode("utf-8")
    encrypted_payload = encrypt_sensitive_field(original_identifier, associated_data=aad)

    mapping = PseudonymMapping(
        organization_id=organization_id,
        token=token,
        encrypted_mapping=encrypted_payload,
        key_version=1,
        purpose=purpose
    )
    db.add(mapping)
    await db.commit()
    await db.refresh(mapping)

    return {
        "token": token,
        "purpose": mapping.purpose,
        "created_at": mapping.created_at.isoformat(),
        "key_version": mapping.key_version,
        "is_new": True
    }


async def reidentify_token(
    db: AsyncSession,
    organization_id: str,
    token: str
) -> Dict[str, Any]:
    """
    Retrieves and decrypts the original identifier from the encrypted mapping vault.
    Must be logged to the immutable audit trail!
    """
    query = select(PseudonymMapping).where(
        PseudonymMapping.organization_id == organization_id,
        PseudonymMapping.token == token
    )
    res = await db.execute(query)
    mapping = res.scalar_one_or_none()

    if not mapping:
        raise ValueError(f"No pseudonym mapping found for token {token}")

    aad = f"org:{organization_id}".encode("utf-8")
    original = decrypt_sensitive_field(mapping.encrypted_mapping, associated_data=aad)

    return {
        "token": token,
        "original_identifier": original,
        "purpose": mapping.purpose,
        "key_version": mapping.key_version
    }
