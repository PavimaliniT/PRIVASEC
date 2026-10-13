from typing import List, Optional, Callable
from fastapi import Request, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.entities import User, Session, Role, Organization, utc_now
from app.core.security import hash_token
from app.config import settings


async def get_current_session_and_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> tuple[Session, User]:
    """
    Extracts session token from HttpOnly cookie or Authorization header,
    validates active status, and returns (Session, User).
    """
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        # Check Authorization Bearer header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. No session token provided."
        )

    token_h = hash_token(token)
    query = (
        select(Session, User, Role)
        .join(User, Session.user_id == User.id)
        .join(Role, User.role_id == Role.id)
        .where(
            Session.token_hash == token_h,
            Session.revoked_at.is_(None),
            Session.expires_at > utc_now()
        )
    )
    result = await db.execute(query)
    row = result.first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or revoked session. Please log in again."
        )

    sess, usr, role = row
    if usr.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {usr.status}. Access denied."
        )

    # Attach to request state for middleware & telemetry
    request.state.user = usr
    request.state.session = sess
    request.state.organization_id = usr.organization_id
    request.state.role = role.name

    return sess, usr


async def get_current_user(
    session_user: tuple[Session, User] = Depends(get_current_session_and_user)
) -> User:
    """Dependency that returns the authenticated User."""
    return session_user[1]


def require_roles(allowed_roles: List[str]):
    """Enforces role-based authorization check."""
    async def role_checker(
        session_user: tuple[Session, User] = Depends(get_current_session_and_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        sess, usr = session_user
        query = select(Role).where(Role.id == usr.role_id)
        res = await db.execute(query)
        role = res.scalar_one_or_none()
        
        if not role or role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden. Required role: {', '.join(allowed_roles)} (Your role: {role.name if role else 'None'})"
            )
        return usr
    return role_checker


def require_step_up_auth():
    """Requires that the current session has completed MFA / step-up verification."""
    async def step_up_checker(
        session_user: tuple[Session, User] = Depends(get_current_session_and_user)
    ) -> User:
        sess, usr = session_user
        if usr.mfa_enabled and not sess.is_mfa_authenticated:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="MFA Step-Up Verification required for this sensitive operation."
            )
        return usr
    return step_up_checker
