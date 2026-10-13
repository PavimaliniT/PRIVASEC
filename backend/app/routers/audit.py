from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models.entities import User, AuditLog
from app.core.rbac import get_current_user, require_roles
from app.core.audit import verify_audit_chain

router = APIRouter(prefix="/audit", tags=["Audit & Cryptographic Compliance"])


@router.get("/logs")
async def list_audit_logs(
    limit: int = 100,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves immutable append-only audit records with previous and entry SHA-256 hashes."""
    query = (
        select(AuditLog)
        .where(AuditLog.organization_id == user.organization_id)
        .order_by(desc(AuditLog.timestamp))
        .limit(limit)
    )
    res = await db.execute(query)
    logs = res.scalars().all()
    return logs


@router.get("/verify")
async def verify_chain(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cryptographically verifies the entire audit ledger hash chain for tampering or omission.
    Recomputes SHA-256 hashes block-by-block from genesis.
    """
    verification_result = await verify_audit_chain(db, user.organization_id)
    return verification_result
