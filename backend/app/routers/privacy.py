from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models.entities import User, PiiScan, PrivacyPolicy, PseudonymMapping
from app.schemas.models_schema import (
    ScanTextRequest, MaskRequest, PseudonymizeRequest, ReidentifyRequest, PrivacyPolicyCreate
)
from app.core.rbac import get_current_user, require_roles
from app.core.audit import record_audit_event
from app.modules.privacy.pii_detector import pii_detector
from app.modules.privacy.data_masker import apply_masking_to_text, mask_entity_value
from app.modules.privacy.pseudonymizer import create_pseudonym_mapping, reidentify_token
from app.modules.privacy.diff_privacy import compute_dp_count, compute_dp_average

router = APIRouter(prefix="/privacy", tags=["Privacy Engineering & PII"])


@router.post("/scan")
async def scan_text(
    req: ScanTextRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Scans text for PII using Presidio with PAN and Aadhaar recognizers."""
    findings = pii_detector.scan_text(req.text)
    
    # Compute counts
    counts = {}
    for f in findings:
        t = f["entity_type"]
        counts[t] = counts.get(t, 0) + 1

    # Save scan record
    scan = PiiScan(
        organization_id=user.organization_id,
        created_by=user.id,
        filename="interactive_text_scan",
        entity_counts=counts,
        scan_summary={"total_entities": len(findings), "text_length": len(req.text)}
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)

    return {
        "scan_id": scan.id,
        "total_detected": len(findings),
        "entity_counts": counts,
        "findings": findings
    }


@router.post("/scan-file")
async def scan_file(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Scans uploaded files (TXT, CSV, JSON, PDF) for sensitive personal data."""
    # Read up to 5MB in memory
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds maximum 5MB size limit.")

    extracted_text, findings = pii_detector.scan_file_content(file.filename, content)

    counts = {}
    for f in findings:
        t = f["entity_type"]
        counts[t] = counts.get(t, 0) + 1

    masked_preview = apply_masking_to_text(extracted_text[:1000], findings)

    scan = PiiScan(
        organization_id=user.organization_id,
        created_by=user.id,
        filename=file.filename,
        entity_counts=counts,
        scan_summary={"total_entities": len(findings), "filesize_bytes": len(content)}
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)

    return {
        "scan_id": scan.id,
        "filename": file.filename,
        "filesize_bytes": len(content),
        "total_detected": len(findings),
        "entity_counts": counts,
        "findings": findings[:100],  # Return up to 100 findings
        "masked_preview": masked_preview
    }


@router.post("/mask")
async def mask_data(
    req: MaskRequest,
    user: User = Depends(get_current_user)
):
    """Detects and masks sensitive entities in text using specified strategy."""
    findings = pii_detector.scan_text(req.text)
    masked_output = apply_masking_to_text(req.text, findings, default_strategy=req.strategy)

    return {
        "strategy": req.strategy,
        "original_text": req.text,
        "masked_text": masked_output,
        "entities_transformed": len(findings)
    }


@router.post("/pseudonymize")
async def pseudonymize_identifier(
    req: PseudonymizeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Replaces identifier with domain-separated HMAC pseudonym and stores mapping in vault."""
    result = await create_pseudonym_mapping(
        db=db,
        organization_id=user.organization_id,
        original_identifier=req.identifier,
        purpose=req.purpose,
        deterministic=req.deterministic
    )
    return result


@router.post("/reidentify")
async def reidentify_identifier(
    req: ReidentifyRequest,
    user: User = Depends(require_roles(["privacy_officer", "super_admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Access-controlled re-identification from the encrypted vault.
    Strictly audited and restricted to Privacy Officers and Super Admins.
    """
    try:
        mapping = await reidentify_token(db, user.organization_id, req.token)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Audit log entry with hash chain
    await record_audit_event(
        db=db,
        organization_id=user.organization_id,
        actor_id=user.id,
        action="AUTHORIZED_REIDENTIFICATION",
        metadata={
            "token": req.token,
            "justification": req.justification,
            "user_email": user.email
        }
    )

    return mapping


@router.get("/diff-privacy-demo")
async def differential_privacy_demo(
    epsilon: float = 1.0,
    actual_count: int = 1500,
    user: User = Depends(get_current_user)
):
    """Demonstrates differential privacy Laplace mechanism for aggregate metrics."""
    res = compute_dp_count(actual_count=actual_count, epsilon=epsilon)
    return res


@router.get("/scans")
async def list_scans(
    limit: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists recent PII scans for the organization."""
    query = (
        select(PiiScan)
        .where(PiiScan.organization_id == user.organization_id)
        .order_by(desc(PiiScan.created_at))
        .limit(limit)
    )
    res = await db.execute(query)
    scans = res.scalars().all()
    return scans
