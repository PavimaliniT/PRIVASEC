import os
import secrets
import hashlib
from typing import Dict, Any, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config import settings


class CryptographyService:
    def __init__(self):
        self.master_key = bytes.fromhex(settings.ENCRYPTION_MASTER_KEY_HEX)
        self.key_version = 1

    def generate_random_aes_key(self) -> str:
        """Generates a fresh 256-bit AES key formatted in hex."""
        return secrets.token_hex(32)

    def encrypt_text(self, plaintext: str, key_hex: str = None) -> Dict[str, Any]:
        """
        Encrypts text using AES-256-GCM with a fresh unique 12-byte nonce.
        Returns ciphertext_hex, nonce_hex, tag_hex, algorithm, key_version.
        """
        key = bytes.fromhex(key_hex) if key_hex else self.master_key
        if len(key) != 32:
            raise ValueError("AES-256 requires exactly 32-byte (64 hex characters) key")

        aesgcm = AESGCM(key)
        nonce = secrets.token_bytes(12)  # 96-bit unique nonce
        
        # AESGCM.encrypt appends 16-byte tag to the ciphertext
        encrypted_data = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        ciphertext = encrypted_data[:-16]
        tag = encrypted_data[-16:]

        return {
            "algorithm": "AES-256-GCM",
            "key_version": self.key_version,
            "nonce_hex": nonce.hex(),
            "tag_hex": tag.hex(),
            "ciphertext_hex": ciphertext.hex(),
            "combined_payload_hex": (nonce + encrypted_data).hex(),
            "plaintext_length": len(plaintext)
        }

    def decrypt_text(self, nonce_hex: str, ciphertext_hex: str, tag_hex: str, key_hex: str = None) -> str:
        """
        Decrypts AES-256-GCM ciphertext after validating authentication tag.
        Rejects tampered data securely.
        """
        key = bytes.fromhex(key_hex) if key_hex else self.master_key
        if len(key) != 32:
            raise ValueError("AES-256 requires exactly 32-byte key")

        try:
            nonce = bytes.fromhex(nonce_hex)
            ciphertext = bytes.fromhex(ciphertext_hex)
            tag = bytes.fromhex(tag_hex)
            full_encrypted = ciphertext + tag

            aesgcm = AESGCM(key)
            plaintext_bytes = aesgcm.decrypt(nonce, full_encrypted, None)
            return plaintext_bytes.decode("utf-8")
        except Exception as e:
            raise ValueError(f"Decryption authentication failed. Ciphertext or tag has been tampered with or key is invalid: {str(e)}")

    def encrypt_file_bytes(self, data: bytes, key_hex: str = None) -> Tuple[bytes, Dict[str, Any]]:
        """Encrypts binary file payload with AES-256-GCM."""
        key = bytes.fromhex(key_hex) if key_hex else self.master_key
        aesgcm = AESGCM(key)
        nonce = secrets.token_bytes(12)
        encrypted_data = aesgcm.encrypt(nonce, data, None)
        
        # Format: 12 bytes nonce + encrypted_data (including 16 bytes tag at end)
        output_bytes = nonce + encrypted_data
        sha256_hash = hashlib.sha256(data).hexdigest()

        meta = {
            "algorithm": "AES-256-GCM",
            "key_version": self.key_version,
            "original_size": len(data),
            "encrypted_size": len(output_bytes),
            "original_sha256": sha256_hash,
            "nonce_hex": nonce.hex()
        }
        return output_bytes, meta

    def decrypt_file_bytes(self, encrypted_file_bytes: bytes, key_hex: str = None) -> Tuple[bytes, Dict[str, Any]]:
        """Decrypts binary file payload with AES-256-GCM."""
        if len(encrypted_file_bytes) < 28:  # 12 nonce + 16 tag minimum
            raise ValueError("Encrypted payload is corrupted or too short")

        key = bytes.fromhex(key_hex) if key_hex else self.master_key
        nonce = encrypted_file_bytes[:12]
        ciphertext_and_tag = encrypted_file_bytes[12:]

        try:
            aesgcm = AESGCM(key)
            decrypted = aesgcm.decrypt(nonce, ciphertext_and_tag, None)
            return decrypted, {
                "decrypted_size": len(decrypted),
                "sha256": hashlib.sha256(decrypted).hexdigest()
            }
        except Exception as e:
            raise ValueError(f"Decryption failed: integrity check violated or invalid key: {str(e)}")

    def compute_hashes_and_verify(self, data: bytes, expected_sha256: str = None) -> Dict[str, Any]:
        """Computes SHA-256 and SHA-512 hashes and verifies integrity against expected hash."""
        sha256 = hashlib.sha256(data).hexdigest()
        sha512 = hashlib.sha512(data).hexdigest()
        
        verified = None
        if expected_sha256:
            verified = (sha256.lower() == expected_sha256.lower().strip())

        return {
            "sha256": sha256,
            "sha512": sha512,
            "byte_size": len(data),
            "verified": verified
        }


crypto_service = CryptographyService()
