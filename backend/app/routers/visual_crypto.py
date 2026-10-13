from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from app.models.entities import User
from app.core.rbac import get_current_user
from app.modules.cryptography.visual_crypto import visual_crypto_service

router = APIRouter(prefix="/visual-crypto", tags=["Visual Cryptography Lab"])


@router.post("/split")
async def split_image_endpoint(
    file: UploadFile = File(...),
    threshold: int = Form(128),
    user: User = Depends(get_current_user)
):
    """
    Splits uploaded secret image into two random 2-out-of-2 visual secret sharing shares.
    Neither share independently reveals any visual information.
    """
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image must be under 5MB.")

    try:
        result = visual_crypto_service.split_secret_image(content, threshold=threshold)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process secret image: {str(e)}")


@router.post("/reconstruct")
async def reconstruct_shares_endpoint(
    share1: UploadFile = File(...),
    share2: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    """Superimposes and visually reconstructs the secret image from two shares."""
    s1_bytes = await share1.read()
    s2_bytes = await share2.read()

    try:
        result = visual_crypto_service.reconstruct_from_shares(s1_bytes, s2_bytes)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to reconstruct shares: {str(e)}")
