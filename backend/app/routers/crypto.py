from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response
from app.models.entities import User
from app.schemas.models_schema import EncryptTextRequest, DecryptTextRequest, HashVerifyRequest
from app.core.rbac import get_current_user
from app.modules.cryptography.aes_gcm import crypto_service

router = APIRouter(prefix="/crypto", tags=["Cryptography Suite"])


@router.get("/generate-key")
async def generate_key(user: User = Depends(get_current_user)):
    """Generates a fresh 256-bit AES key formatted in hexadecimal."""
    return {"key_hex": crypto_service.generate_random_aes_key(), "algorithm": "AES-256-GCM"}


@router.post("/encrypt-text")
async def encrypt_text_endpoint(
    req: EncryptTextRequest,
    user: User = Depends(get_current_user)
):
    """Encrypts plaintext with AES-256-GCM using unique nonce."""
    try:
        return crypto_service.encrypt_text(req.plaintext, key_hex=req.key_hex)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/decrypt-text")
async def decrypt_text_endpoint(
    req: DecryptTextRequest,
    user: User = Depends(get_current_user)
):
    """Decrypts ciphertext with authentication tag verification."""
    try:
        plaintext = crypto_service.decrypt_text(
            nonce_hex=req.nonce_hex,
            ciphertext_hex=req.ciphertext_hex,
            tag_hex=req.tag_hex,
            key_hex=req.key_hex
        )
        return {"plaintext": plaintext, "authenticated": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/encrypt-file")
async def encrypt_file_endpoint(
    file: UploadFile = File(...),
    key_hex: str = Form(None),
    user: User = Depends(get_current_user)
):
    """Encrypts binary file payload with AES-256-GCM."""
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds 10MB limit.")

    enc_bytes, meta = crypto_service.encrypt_file_bytes(content, key_hex=key_hex)
    
    # Return as downloadable binary file with metadata headers
    return Response(
        content=enc_bytes,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{file.filename}.privasec.enc"',
            "X-Privasec-Algorithm": meta["algorithm"],
            "X-Privasec-Nonce": meta["nonce_hex"],
            "X-Privasec-Sha256": meta["original_sha256"]
        }
    )


@router.post("/decrypt-file")
async def decrypt_file_endpoint(
    file: UploadFile = File(...),
    key_hex: str = Form(None),
    user: User = Depends(get_current_user)
):
    """Decrypts AES-256-GCM encrypted file."""
    content = await file.read()
    try:
        dec_bytes, meta = crypto_service.decrypt_file_bytes(content, key_hex=key_hex)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    original_name = file.filename.replace(".privasec.enc", "")
    return Response(
        content=dec_bytes,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{original_name}"',
            "X-Privasec-Decrypted-Sha256": meta["sha256"]
        }
    )


@router.post("/hash")
async def compute_hash_endpoint(
    req: HashVerifyRequest,
    user: User = Depends(get_current_user)
):
    """Computes SHA-256 & SHA-512 hashes and verifies integrity against expected value."""
    result = crypto_service.compute_hashes_and_verify(
        req.text.encode("utf-8"),
        expected_sha256=req.expected_sha256
    )
    return result
