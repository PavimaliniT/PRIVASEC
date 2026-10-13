import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


def generate_uuid():
    return str(uuid.uuid4())


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    settings = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    roles = relationship("Role", back_populates="organization", cascade="all, delete-orphan")
    security_events = relationship("SecurityEvent", back_populates="organization", cascade="all, delete-orphan")
    pii_scans = relationship("PiiScan", back_populates="organization", cascade="all, delete-orphan")
    privacy_policies = relationship("PrivacyPolicy", back_populates="organization", cascade="all, delete-orphan")
    pseudonym_mappings = relationship("PseudonymMapping", back_populates="organization", cascade="all, delete-orphan")
    behavior_profiles = relationship("BehaviorProfile", back_populates="organization", cascade="all, delete-orphan")
    anomalies = relationship("Anomaly", back_populates="organization", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="organization", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="organization", cascade="all, delete-orphan")
    api_clients = relationship("ApiClient", back_populates="organization", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="organization", cascade="all, delete-orphan")


class Role(Base):
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)  # super_admin, security_analyst, privacy_officer, standard_user
    permissions = Column(JSON, default=list)

    organization = relationship("Organization", back_populates="roles")
    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(String(36), ForeignKey("roles.id"), nullable=False)
    mfa_enabled = Column(Boolean, default=False)
    totp_secret_encrypted = Column(Text, nullable=True)
    pseudonym = Column(String(64), index=True, nullable=True)
    status = Column(String(32), default="active")  # active, locked, restricted
    created_at = Column(DateTime(timezone=True), default=utc_now)

    organization = relationship("Organization", back_populates="users")
    role = relationship("Role", back_populates="users")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    device_hash = Column(String(64), nullable=False)
    ip_token = Column(String(64), nullable=False)
    is_mfa_authenticated = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    user = relationship("User", back_populates="sessions")


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_pseudonym = Column(String(64), index=True, nullable=False)
    event_type = Column(String(100), index=True, nullable=False)  # AUTH_LOGIN_SUCCESS, AUTH_LOGIN_FAILURE, API_BURST, etc.
    severity = Column(String(32), default="low")  # low, medium, high, critical
    source = Column(String(100), default="gateway")  # authentication, gateway, privacy, simulation
    network_meta = Column(JSON, default=dict)  # ip_token, country_code
    device_meta = Column(JSON, default=dict)   # device_hash, recognized
    metrics = Column(JSON, default=dict)       # requests_per_minute, failed_logins_5m, etc.
    metadata_redacted = Column(JSON, default=dict)
    sensitivity = Column(String(32), default="low")  # low, medium, high, critical
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)

    organization = relationship("Organization", back_populates="security_events")
    anomaly = relationship("Anomaly", back_populates="event", uselist=False, cascade="all, delete-orphan")
    risk_assessment = relationship("RiskAssessment", back_populates="event", uselist=False, cascade="all, delete-orphan")


class PiiScan(Base):
    __tablename__ = "pii_scans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(String(36), nullable=False)
    filename = Column(String(255), nullable=True)
    status = Column(String(32), default="completed")  # pending, completed, failed
    entity_counts = Column(JSON, default=dict)
    scan_summary = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    organization = relationship("Organization", back_populates="pii_scans")


class PrivacyPolicy(Base):
    __tablename__ = "privacy_policies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False)  # EMAIL_ADDRESS, PHONE_NUMBER, PAN_NUMBER, AADHAAR_NUMBER, etc.
    transformation = Column(String(50), default="MASK")  # MASK, REDACT, PSEUDONYMIZE, ENCRYPT
    masking_strategy = Column(String(50), default="PARTIAL")  # FULL, PARTIAL, REDACT, FORMAT_PRESERVING
    retention_days = Column(Integer, default=90)
    is_active = Column(Boolean, default=True)

    organization = relationship("Organization", back_populates="privacy_policies")


class PseudonymMapping(Base):
    __tablename__ = "pseudonym_mappings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(64), unique=True, index=True, nullable=False)
    encrypted_mapping = Column(Text, nullable=False)  # AES-256-GCM encrypted original identifier
    key_version = Column(Integer, default=1)
    purpose = Column(String(100), default="analytics")
    created_at = Column(DateTime(timezone=True), default=utc_now)

    organization = relationship("Organization", back_populates="pseudonym_mappings")


class BehaviorProfile(Base):
    __tablename__ = "behavior_profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_pseudonym = Column(String(64), index=True, nullable=False)
    baseline_features = Column(JSON, default=dict)  # typical hours, typical devices, avg req/min, etc.
    recent_activity = Column(JSON, default=list)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    organization = relationship("Organization", back_populates="behavior_profiles")


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(String(36), ForeignKey("security_events.id", ondelete="CASCADE"), nullable=False, unique=True)
    model_version = Column(String(50), default="v1.0-isolation-forest")
    anomaly_score = Column(Float, nullable=False)  # Normalized 0-100
    is_anomaly = Column(Boolean, default=False)
    reasons = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    organization = relationship("Organization", back_populates="anomalies")
    event = relationship("SecurityEvent", back_populates="anomaly")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(String(36), ForeignKey("security_events.id", ondelete="CASCADE"), nullable=False, unique=True)
    score = Column(Float, nullable=False)  # 0 - 100
    level = Column(String(32), nullable=False)  # low (0-29), medium (30-59), high (60-79), critical (80-100)
    contributing_factors = Column(JSON, default=dict)  # breakdown of the 5 factor scores and explanations
    recommended_action = Column(String(100), nullable=False)  # ALLOW, REQUIRE_MFA, RESTRICT, REVOKE_SESSION, CREATE_INCIDENT
    created_at = Column(DateTime(timezone=True), default=utc_now)

    organization = relationship("Organization", back_populates="risk_assessments")
    event = relationship("SecurityEvent", back_populates="risk_assessment")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    severity = Column(String(32), default="medium")  # low, medium, high, critical
    status = Column(String(32), default="Detected")  # Detected, Triaged, Investigating, Contained, Resolved, Closed
    risk_score = Column(Float, default=0.0)
    assigned_to = Column(String(255), nullable=True)
    event_id = Column(String(36), nullable=True)
    timeline = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    organization = relationship("Organization", back_populates="incidents")
    actions = relationship("IncidentAction", back_populates="incident", cascade="all, delete-orphan")


class IncidentAction(Base):
    __tablename__ = "incident_actions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = Column(String(100), nullable=False)  # REVOKE_SESSION, REQUIRE_STEP_UP, THROTTLE_IP, LOCK_ACCOUNT, NOTIFY_ANALYST
    status = Column(String(32), default="PENDING")  # PENDING, EXECUTED, ROLLED_BACK, REJECTED
    parameters = Column(JSON, default=dict)
    approved_by = Column(String(255), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    rollback_at = Column(DateTime(timezone=True), nullable=True)

    incident = relationship("Incident", back_populates="actions")


class ApiClient(Base):
    __tablename__ = "api_clients"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    client_name = Column(String(100), nullable=False)
    key_hash = Column(String(64), unique=True, index=True, nullable=False)
    key_prefix = Column(String(16), nullable=False)
    scopes = Column(JSON, default=list)
    status = Column(String(32), default="active")  # active, restricted, revoked
    rate_limit = Column(Integer, default=60)  # requests per minute
    created_at = Column(DateTime(timezone=True), default=utc_now)

    organization = relationship("Organization", back_populates="api_clients")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id = Column(String(255), nullable=False)
    action = Column(String(100), nullable=False)
    metadata_redacted = Column(JSON, default=dict)
    previous_hash = Column(String(64), nullable=False)
    entry_hash = Column(String(64), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)

    organization = relationship("Organization", back_populates="audit_logs")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model_name = Column(String(100), nullable=False)  # isolation_forest_anomaly_detector
    version = Column(String(50), nullable=False)      # v1.0.0
    metrics = Column(JSON, default=dict)             # precision, recall, f1, contamination, train_size
    artifact_path = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
