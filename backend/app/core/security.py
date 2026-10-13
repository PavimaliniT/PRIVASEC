import os
import hashlib
import secrets
from typing import Optional, Tuple
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
import pyotp
import qrcode
import io
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config import settings

# Argon2id password hasher
ph = PasswordHasher(
    time_cost=2,
    memory_cost=65536,  # 64 MB
    parallelism=2,
    hash_len=32,
    salt_len=16
)


def hash_password(password: str) -> str:
    """Hashes a password with Argon2id."""
    return ph.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verifies a password against an Argon2id hash."""
    try:
        return ph.verify(hashed_password, password)
    except (VerifyMismatchError, VerificationError):
        return False


def hash_token(token: str) -> str:
    """Computes SHA-256 hash of a session token or API key for secure lookup."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_secure_token(nbytes: int = 32) -> str:
    """Generates a high-entropy URL-safe token."""
    return secrets.token_urlsafe(nbytes)


# KMS AES-256-GCM Envelope/Field encryption
def get_master_aes_key() -> bytes:
    """Returns the 32-byte AES-256 master key."""
    return bytes.fromhex(settings.ENCRYPTION_MASTER_KEY_HEX)


def encrypt_sensitive_field(plaintext: str, associated_data: Optional[bytes] = None) -> str:
    """
    Encrypts a field with AES-256-GCM.
    Returns format: nonce_hex:ciphertext_hex
    """
    key = get_master_aes_key()
    aesgcm = AESGCM(key)
    nonce = secrets.token_bytes(12)  # 96-bit unique nonce
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), associated_data)
    return f"{nonce.hex()}:{ciphertext.hex()}"


def decrypt_sensitive_field(encrypted_str: str, associated_data: Optional[bytes] = None) -> str:
    """
    Decrypts an AES-256-GCM encrypted field.
    Expects format: nonce_hex:ciphertext_hex
    """
    try:
        parts = encrypted_str.split(":")
        if len(parts) != 2:
            raise ValueError("Malformed encrypted payload")
        nonce = bytes.fromhex(parts[0])
        ciphertext = bytes.fromhex(parts[1])
        key = get_master_aes_key()
        aesgcm = AESGCM(key)
        plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, associated_data)
        return plaintext_bytes.decode("utf-8")
    except Exception as e:
        raise ValueError(f"Decryption failed or authentication tag mismatch: {str(e)}")


# TOTP MFA helpers
def generate_totp_secret() -> str:
    """Generates a base32 TOTP secret."""
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str) -> str:
    """Generates a TOTP provisioning URI."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name="PRIVASEC")


def generate_totp_qr_base64(secret: str, email: str) -> str:
    """Generates a base64 encoded PNG QR code image for TOTP setup."""
    uri = get_totp_uri(secret, email)
    qr = qrcode.QRCode(
        version=1,
        box_size=6,
        border=2,
        error_correction=qrcode.constants.ERROR_CORRECT_M
    )
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def verify_totp_code(secret: str, code: str) -> bool:
    """Verifies a 6-digit TOTP code with standard 1-step window."""
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)
