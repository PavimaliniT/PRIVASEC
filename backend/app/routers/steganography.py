from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from app.models.entities import User
from app.core.rbac import get_current_user
from app.modules.cryptography.steganography import steganography_service

router = APIRouter(prefix="/steganography", tags=["Steganography Lab"])


@router.post("/embed")
async def embed_message_endpoint(
    cover_image: UploadFile = File(...),
    secret_message: str = Form(...),
    key_hex: str = Form(None),
    user: User = Depends(get_current_user)
):
    """Embeds an AES-256-GCM authenticated secret message into the LSBs of a lossless PNG."""
    if not cover_image.filename.lower().endswith(".png"):
        raise HTTPException(status_code=400, detail="Steganography requires lossless PNG cover image.")

    content = await cover_image.read()
    try:
        result = steganography_service.embed_secret_message(
            cover_image_bytes=content,
            secret_message=secret_message,
            encryption_key_hex=key_hex
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/extract")
async def extract_message_endpoint(
    stego_image: UploadFile = File(...),
    key_hex: str = Form(None),
    user: User = Depends(get_current_user)
):
    """Extracts and decrypts secret message hidden in PNG LSBs."""
    content = await stego_image.read()
    try:
        result = steganography_service.extract_secret_message(
            stego_image_bytes=content,
            decryption_key_hex=key_hex
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/compare")
async def compare_images_endpoint(
    cover_image: UploadFile = File(...),
    stego_image: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    """Compares original cover PNG with stego PNG and computes PSNR and difference map."""
    c_bytes = await cover_image.read()
    s_bytes = await stego_image.read()

    try:
        result = steganography_service.compare_images(c_bytes, s_bytes)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
