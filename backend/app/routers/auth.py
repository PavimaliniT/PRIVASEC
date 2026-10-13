from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.database import get_db
from app.models.entities import User, Role, Session, Organization, utc_now
from app.schemas.models_schema import (
    RegisterRequest, LoginRequest, UserResponse, SessionResponse,
    MfaSetupResponse, MfaVerifyRequest, StepUpRequest
)
from app.core.security import (
    hash_password, verify_password, hash_token, generate_secure_token,
    generate_totp_secret, generate_totp_qr_base64, verify_totp_code,
    encrypt_sensitive_field, decrypt_sensitive_field
)
from app.core.rbac import get_current_user, get_current_session_and_user
from app.core.audit import record_audit_event
from app.core.event_bus import emit_security_event
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication & Access Control"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Registers a new user within an organization."""
    # Check if user already exists
    existing = await db.execute(select(User).where(User.email == req.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    # Find or create organization
    org_res = await db.execute(select(Organization).where(Organization.name == req.organization_name))
    org = org_res.scalar_one_or_none()
    if not org:
        org = Organization(name=req.organization_name or "Default Cyber Defense Org")
        db.add(org)
        await db.commit()
        await db.refresh(org)

    # Find or create role
    role_res = await db.execute(
        select(Role).where(Role.organization_id == org.id, Role.name == req.role_name)
    )
    role = role_res.scalar_one_or_none()
    if not role:
        role = Role(organization_id=org.id, name=req.role_name, permissions=["read", "investigate"])
        db.add(role)
        await db.commit()
        await db.refresh(role)

    # Deterministic pseudonym prefix for the actor
    import hashlib
    pseudo = "usr_" + hashlib.sha256(req.email.lower().encode()).hexdigest()[:8]

    user = User(
        organization_id=org.id,
        email=req.email.lower(),
        password_hash=hash_password(req.password),
        role_id=role.id,
        pseudonym=pseudo,
        mfa_enabled=False
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    await record_audit_event(
        db=db,
        organization_id=org.id,
        actor_id=user.id,
        action="USER_REGISTRATION",
        metadata={"email": user.email, "role": role.name}
    )

    return {
        "message": "User registered successfully",
        "user_id": user.id,
        "email": user.email,
        "role": role.name
    }


@router.post("/login")
async def login(
    req: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticates user, validates rate limits, evaluates contextual risk,
    and sets secure session cookie.
    """
    client_ip = getattr(request.state, "client_ip", "127.0.0.1")
    ip_token = getattr(request.state, "ip_token", "ip_unknown")
    device_hash = getattr(request.state, "device_hash", "dev_unknown")

    # Find user
    query = (
        select(User, Role, Organization)
        .join(Role, User.role_id == Role.id)
        .join(Organization, User.organization_id == Organization.id)
        .where(User.email == req.email.lower())
    )
    res = await db.execute(query)
    row = res.first()

    if not row:
        # Emit failed auth security event
        await emit_security_event(
            db=db,
            organization_id="default_org",
            actor_pseudonym=f"unknown_{ip_token[:6]}",
            event_type="AUTH_LOGIN_FAILED_UNKNOWN_USER",
            source="authentication",
            severity="medium",
            network={"ip_token": ip_token, "client_ip": client_ip},
            device={"device_hash": device_hash},
            metrics={"failed_logins_5m": 1}
        )
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    user, role, org = row

    if not verify_password(req.password, user.password_hash):
        event_res = await emit_security_event(
            db=db,
            organization_id=org.id,
            actor_pseudonym=user.pseudonym or f"usr_{user.id[:6]}",
            event_type="AUTH_LOGIN_FAILED_BAD_PASSWORD",
            source="authentication",
            severity="high",
            network={"ip_token": ip_token},
            device={"device_hash": device_hash},
            metrics={"failed_logins_5m": 3},
            user_id=user.id
        )
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    # Check MFA requirement
    mfa_verified = False
    if user.mfa_enabled:
        if not req.totp_code:
            return {
                "mfa_required": True,
                "message": "TOTP MFA challenge required to complete authentication.",
                "user_id": user.id
            }
        
        # Verify TOTP
        decrypted_secret = decrypt_sensitive_field(user.totp_secret_encrypted)
        if not verify_totp_code(decrypted_secret, req.totp_code):
            raise HTTPException(status_code=401, detail="Invalid TOTP authentication code.")
        mfa_verified = True

    # Generate secure session token
    token = generate_secure_token(32)
    token_h = hash_token(token)
    expires_at = utc_now() + timedelta(seconds=settings.SESSION_MAX_AGE_SECONDS)

    sess = Session(
        user_id=user.id,
        token_hash=token_h,
        device_hash=device_hash,
        ip_token=ip_token,
        is_mfa_authenticated=mfa_verified,
        expires_at=expires_at
    )
    db.add(sess)
    await db.commit()

    # Set secure HttpOnly cookie
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.SESSION_MAX_AGE_SECONDS,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        path="/"
    )

    # Emit successful login event
    event_result = await emit_security_event(
        db=db,
        organization_id=org.id,
        actor_pseudonym=user.pseudonym or f"usr_{user.id[:6]}",
        event_type="AUTH_LOGIN_SUCCESS",
        source="authentication",
        severity="low",
        network={"ip_token": ip_token},
        device={"device_hash": device_hash},
        metrics={"failed_logins_5m": 0, "requests_per_minute": 10.0},
        user_id=user.id
    )

    return {
        "message": "Authentication successful",
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "role": role.name,
            "pseudonym": user.pseudonym,
            "mfa_enabled": user.mfa_enabled,
            "organization_id": org.id,
            "organization_name": org.name
        },
        "session": {
            "id": sess.id,
            "is_mfa_authenticated": mfa_verified,
            "expires_at": expires_at.isoformat()
        },
        "telemetry_risk": event_result.get("risk")
    }


@router.get("/me")
async def get_me(
    session_user: tuple[Session, User] = Depends(get_current_session_and_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns currently authenticated user profile and session security state."""
    sess, user = session_user
    role_res = await db.execute(select(Role).where(Role.id == user.role_id))
    role = role_res.scalar_one_or_none()

    return {
        "id": user.id,
        "email": user.email,
        "role": role.name if role else "standard_user",
        "organization_id": user.organization_id,
        "pseudonym": user.pseudonym,
        "mfa_enabled": user.mfa_enabled,
        "session": {
            "id": sess.id,
            "device_hash": sess.device_hash,
            "ip_token": sess.ip_token,
            "is_mfa_authenticated": sess.is_mfa_authenticated,
            "expires_at": sess.expires_at.isoformat()
        }
    }


@router.post("/mfa/setup", response_model=MfaSetupResponse)
async def setup_mfa(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generates a new TOTP secret and QR code for MFA enrollment."""
    secret = generate_totp_secret()
    qr_b64 = generate_totp_qr_base64(secret, user.email)
    
    # Store provisionally
    user.totp_secret_encrypted = encrypt_sensitive_field(secret)
    await db.commit()

    return {
        "secret": secret,
        "qr_code_base64": qr_b64,
        "provisioning_uri": f"otpauth://totp/PRIVASEC:{user.email}?secret={secret}&issuer=PRIVASEC"
    }


@router.post("/mfa/verify")
async def verify_mfa_setup(
    req: MfaVerifyRequest,
    session_user: tuple[Session, User] = Depends(get_current_session_and_user),
    db: AsyncSession = Depends(get_db)
):
    """Verifies initial 6-digit TOTP code and activates MFA on the account."""
    sess, user = session_user
    if not user.totp_secret_encrypted:
        raise HTTPException(status_code=400, detail="MFA setup has not been initiated.")

    secret = decrypt_sensitive_field(user.totp_secret_encrypted)
    if not verify_totp_code(secret, req.totp_code):
        raise HTTPException(status_code=400, detail="Invalid 6-digit TOTP code.")

    user.mfa_enabled = True
    sess.is_mfa_authenticated = True
    await db.commit()

    await record_audit_event(
        db=db,
        organization_id=user.organization_id,
        actor_id=user.id,
        action="MFA_ENABLED",
        metadata={"email": user.email}
    )

    return {"message": "Multifactor authentication successfully verified and enabled."}


@router.post("/step-up")
async def step_up_auth(
    req: StepUpRequest,
    session_user: tuple[Session, User] = Depends(get_current_session_and_user),
    db: AsyncSession = Depends(get_db)
):
    """Provides elevated step-up authentication for high-risk actions."""
    sess, user = session_user
    if not user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA is not enabled on this account.")

    secret = decrypt_sensitive_field(user.totp_secret_encrypted)
    if not verify_totp_code(secret, req.totp_code):
        raise HTTPException(status_code=400, detail="Invalid step-up verification code.")

    sess.is_mfa_authenticated = True
    await db.commit()

    return {"message": "Step-up verification approved. Session elevated."}


@router.post("/logout")
async def logout(
    response: Response,
    session_user: tuple[Session, User] = Depends(get_current_session_and_user),
    db: AsyncSession = Depends(get_db)
):
    """Revokes current session and clears cookie."""
    sess, _ = session_user
    sess.revoked_at = utc_now()
    await db.commit()

    response.delete_cookie(key=settings.SESSION_COOKIE_NAME, path="/")
    return {"message": "Logged out successfully"}
