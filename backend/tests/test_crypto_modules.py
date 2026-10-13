import pytest
import io
import numpy as np
from PIL import Image
from app.modules.cryptography.aes_gcm import crypto_service
from app.modules.cryptography.visual_crypto import visual_crypto_service
from app.modules.cryptography.steganography import steganography_service


def test_aes_gcm_round_trip():
    """Verifies AES-256-GCM encryption and decryption round-trip."""
    plaintext = "PRIVASEC Confidential Security Directive #409"
    encrypted = crypto_service.encrypt_text(plaintext)
    
    assert "nonce_hex" in encrypted
    assert "ciphertext_hex" in encrypted
    assert "tag_hex" in encrypted
    assert len(encrypted["nonce_hex"]) == 24  # 12 bytes = 24 hex

    decrypted = crypto_service.decrypt_text(
        nonce_hex=encrypted["nonce_hex"],
        ciphertext_hex=encrypted["ciphertext_hex"],
        tag_hex=encrypted["tag_hex"]
    )
    assert decrypted == plaintext


def test_aes_gcm_tamper_rejection():
    """Verifies that tampered ciphertext or altered authentication tag is strictly rejected."""
    plaintext = "Top Secret Key Material"
    encrypted = crypto_service.encrypt_text(plaintext)

    # Tamper with the ciphertext by flipping one byte
    tampered_ct = list(encrypted["ciphertext_hex"])
    tampered_ct[0] = "f" if tampered_ct[0] != "f" else "0"
    tampered_hex = "".join(tampered_ct)

    with pytest.raises(ValueError, match="Decryption authentication failed"):
        crypto_service.decrypt_text(
            nonce_hex=encrypted["nonce_hex"],
            ciphertext_hex=tampered_hex,
            tag_hex=encrypted["tag_hex"]
        )


def test_visual_cryptography_split_and_reconstruct():
    """Tests 2-out-of-2 visual secret sharing: splitting image and verifying overlay."""
    # Create a simple synthetic 16x16 binary test image (black square on white background)
    test_arr = np.ones((16, 16), dtype=np.uint8) * 255
    test_arr[4:12, 4:12] = 0  # Black square
    img = Image.fromarray(test_arr)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    result = visual_crypto_service.split_secret_image(img_bytes, threshold=128)
    assert "share1_png_base64" in result
    assert "share2_png_base64" in result
    assert result["share_width"] == 32
    assert result["share_height"] == 32

    # Reconstruct
    import base64
    s1_bytes = base64.b64decode(result["share1_png_base64"])
    s2_bytes = base64.b64decode(result["share2_png_base64"])
    recon = visual_crypto_service.reconstruct_from_shares(s1_bytes, s2_bytes)
    assert "reconstructed_png_base64" in recon
    assert recon["width"] == 32
    assert recon["height"] == 32


def test_steganography_embed_and_extract():
    """Tests PNG LSB steganography embedding with authenticated encryption and extraction."""
    # Create a 64x64 solid blue PNG cover image
    cover = Image.new("RGB", (64, 64), color=(30, 60, 120))
    buf = io.BytesIO()
    cover.save(buf, format="PNG")
    cover_bytes = buf.getvalue()

    secret = "TopSecret-Stego-Token-987654"
    embed_result = steganography_service.embed_secret_message(cover_bytes, secret)
    assert embed_result["status"] == "SUCCESS"
    assert embed_result["psnr_db"] > 40.0  # High visual fidelity

    # Extract
    import base64
    stego_bytes = base64.b64decode(embed_result["stego_png_base64"])
    extract_result = steganography_service.extract_secret_message(stego_bytes)
    assert extract_result["status"] == "SUCCESS"
    assert extract_result["secret_message"] == secret
