from typing import List, Dict, Any, Optional
from pydantic import BaseModel, EmailStr, Field


# Auth Schemas
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role_name: str = "security_analyst"
    organization_name: Optional[str] = "Acme Cyber Defense"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_code: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    organization_id: str
    mfa_enabled: bool
    pseudonym: Optional[str] = None
    created_at: str


class SessionResponse(BaseModel):
    id: str
    device_hash: str
    ip_token: str
    is_mfa_authenticated: bool
    expires_at: str
    created_at: str


class MfaSetupResponse(BaseModel):
    secret: str
    qr_code_base64: str
    provisioning_uri: str


class MfaVerifyRequest(BaseModel):
    totp_code: str = Field(min_length=6, max_length=6)


class StepUpRequest(BaseModel):
    totp_code: str = Field(min_length=6, max_length=6)


# Privacy Schemas
class ScanTextRequest(BaseModel):
    text: str


class MaskRequest(BaseModel):
    text: str
    strategy: str = "PARTIAL"  # FULL, PARTIAL, REDACT, FORMAT_PRESERVING


class PseudonymizeRequest(BaseModel):
    identifier: str
    purpose: str = "analytics"
    deterministic: bool = True


class ReidentifyRequest(BaseModel):
    token: str
    justification: str = "Security Analyst Incident Investigation"


class PrivacyPolicyCreate(BaseModel):
    entity_type: str
    transformation: str = "MASK"
    masking_strategy: str = "PARTIAL"
    retention_days: int = 90


# Cryptography Schemas
class EncryptTextRequest(BaseModel):
    plaintext: str
    key_hex: Optional[str] = None


class DecryptTextRequest(BaseModel):
    nonce_hex: str
    ciphertext_hex: str
    tag_hex: str
    key_hex: Optional[str] = None


class HashVerifyRequest(BaseModel):
    text: str
    expected_sha256: Optional[str] = None


class StegoEmbedRequest(BaseModel):
    secret_message: str
    key_hex: Optional[str] = None


# Intelligence & Simulation Schemas
class AnomalyAnalyzeRequest(BaseModel):
    requests_per_minute: float = 15.0
    failed_logins_5m: int = 0
    time_of_day_deviation: float = 0.1
    device_novelty: float = 0.0
    endpoint_rarity: float = 0.1
    export_volume_kb: float = 0.0
    access_denial_frequency: float = 0.0


class RiskEvaluateRequest(BaseModel):
    actor_pseudonym: str = "usr_analyst_01"
    event_type: str = "AUTH_LOGIN_ATTEMPT"
    requests_per_minute: float = 20.0
    failed_logins_5m: int = 0
    device_novelty: float = 0.0
    sensitivity: str = "medium"
    export_volume_kb: float = 0.0
    detected_threats: List[str] = []


class IncidentActionRequest(BaseModel):
    action_type: str  # REVOKE_SESSION, REQUIRE_STEP_UP, LOCK_ACCOUNT, ROLLBACK
    reason: str


class IncidentResolveRequest(BaseModel):
    resolution_note: str
    status: str = "Resolved"  # Resolved, Closed
