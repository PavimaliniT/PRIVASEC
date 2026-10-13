import io
import math
import struct
import base64
import numpy as np
from PIL import Image
from typing import Dict, Any, Tuple
from app.modules.cryptography.aes_gcm import crypto_service

MAGIC_HEADER = b"PSEC"  # 4 bytes PRIVASEC magic identifier


class SteganographyService:
    def embed_secret_message(
        self,
        cover_image_bytes: bytes,
        secret_message: str,
        encryption_key_hex: str = None
    ) -> Dict[str, Any]:
        """
        1. Encrypts secret message with AES-256-GCM.
        2. Packages payload: MAGIC (4B) + LENGTH (4B) + NONCE (12B) + CIPHERTEXT + TAG (16B).
        3. Validates PNG capacity.
        4. Embeds payload into LSB of RGB channels.
        5. Computes PSNR and MSE quality metrics.
        """
        cover_img = Image.open(io.BytesIO(cover_image_bytes)).convert("RGB")
        cover_arr = np.array(cover_img)
        h, w, c = cover_arr.shape

        total_bits_available = h * w * c
        total_bytes_capacity = total_bits_available // 8

        # 1. Encrypt message
        enc_res = crypto_service.encrypt_text(secret_message, key_hex=encryption_key_hex)
        nonce_bytes = bytes.fromhex(enc_res["nonce_hex"])
        ct_bytes = bytes.fromhex(enc_res["ciphertext_hex"])
        tag_bytes = bytes.fromhex(enc_res["tag_hex"])
        encrypted_blob = nonce_bytes + ct_bytes + tag_bytes

        # 2. Package payload
        payload_len = len(encrypted_blob)
        header = MAGIC_HEADER + struct.pack(">I", payload_len)
        full_payload = header + encrypted_blob

        if len(full_payload) * 8 > total_bits_available:
            raise ValueError(
                f"Payload ({len(full_payload)} bytes) exceeds cover image capacity ({total_bytes_capacity} bytes). "
                f"Use a larger PNG image or shorter message."
            )

        # Convert payload to bit string
        bits = []
        for byte in full_payload:
            for b in range(8):
                bits.append((byte >> (7 - b)) & 1)

        # 3. LSB embedding into flattened array
        stego_arr = cover_arr.copy()
        flat_stego = stego_arr.reshape(-1)
        
        for idx, bit in enumerate(bits):
            # Clear LSB and write payload bit
            flat_stego[idx] = (int(flat_stego[idx]) & 0xFE) | bit

        stego_arr = flat_stego.reshape((h, w, c))

        # 4. Compute Image Quality Metrics (MSE & PSNR)
        mse = float(np.mean((cover_arr.astype(float) - stego_arr.astype(float)) ** 2))
        if mse == 0.0:
            psnr = 99.0
        else:
            psnr = round(10.0 * math.log10((255.0 ** 2) / mse), 2)

        # Generate base64 stego PNG
        stego_img = Image.fromarray(stego_arr, mode="RGB")
        stego_buf = io.BytesIO()
        stego_img.save(stego_buf, format="PNG")
        stego_b64 = base64.b64encode(stego_buf.getvalue()).decode("utf-8")

        return {
            "status": "SUCCESS",
            "image_dimensions": f"{w}x{h}",
            "capacity_bytes": total_bytes_capacity,
            "payload_bytes": len(full_payload),
            "bits_modified": len(bits),
            "capacity_used_percent": round((len(full_payload) / total_bytes_capacity) * 100, 2),
            "mse": round(mse, 6),
            "psnr_db": psnr,
            "imperceptibility": "Imperceptible" if psnr > 40 else "Low distortion",
            "stego_png_base64": stego_b64,
            "encryption_algorithm": "AES-256-GCM (Authenticated)",
            "nonce_hex": enc_res["nonce_hex"],
            "tag_hex": enc_res["tag_hex"]
        }

    def extract_secret_message(
        self,
        stego_image_bytes: bytes,
        decryption_key_hex: str = None
    ) -> Dict[str, Any]:
        """
        Extracts LSB bitstream, verifies MAGIC_HEADER, unpacks encrypted blob,
        and decrypts using AES-256-GCM.
        """
        stego_img = Image.open(io.BytesIO(stego_image_bytes)).convert("RGB")
        stego_arr = np.array(stego_img)
        flat = stego_arr.reshape(-1)

        # 1. Read first 8 bytes (64 bits) for header (4B magic + 4B length)
        header_bits = [flat[i] & 1 for i in range(64)]
        header_bytes = bytearray()
        for i in range(0, 64, 8):
            b = 0
            for j in range(8):
                b = (b << 1) | header_bits[i + j]
            header_bytes.append(b)

        magic = bytes(header_bytes[:4])
        if magic != MAGIC_HEADER:
            raise ValueError("No PRIVASEC steganographic payload detected in image (Header mismatch).")

        payload_len = struct.unpack(">I", header_bytes[4:8])[0]
        max_possible = (len(flat) - 64) // 8
        if payload_len > max_possible or payload_len <= 28:
            raise ValueError(f"Corrupted or invalid payload length indicator: {payload_len} bytes")

        # 2. Extract payload bits
        total_payload_bits = payload_len * 8
        payload_bits = [flat[64 + i] & 1 for i in range(total_payload_bits)]
        payload_bytes = bytearray()
        for i in range(0, total_payload_bits, 8):
            b = 0
            for j in range(8):
                b = (b << 1) | payload_bits[i + j]
            payload_bytes.append(b)

        # 3. Parse encrypted blob: 12B nonce + ciphertext + 16B tag
        nonce_bytes = bytes(payload_bytes[:12])
        tag_bytes = bytes(payload_bytes[-16:])
        ct_bytes = bytes(payload_bytes[12:-16])

        # 4. Decrypt with AES-256-GCM
        decrypted_message = crypto_service.decrypt_text(
            nonce_hex=nonce_bytes.hex(),
            ciphertext_hex=ct_bytes.hex(),
            tag_hex=tag_bytes.hex(),
            key_hex=decryption_key_hex
        )

        return {
            "status": "SUCCESS",
            "secret_message": decrypted_message,
            "payload_bytes": payload_len,
            "nonce_hex": nonce_bytes.hex(),
            "tag_hex": tag_bytes.hex(),
            "message_length": len(decrypted_message)
        }

    def compare_images(self, cover_bytes: bytes, stego_bytes: bytes) -> Dict[str, Any]:
        """Calculates difference matrix and metrics between cover and stego images."""
        c_img = Image.open(io.BytesIO(cover_bytes)).convert("RGB")
        s_img = Image.open(io.BytesIO(stego_bytes)).convert("RGB")

        c_arr = np.array(c_img)
        s_arr = np.array(s_img)

        if c_arr.shape != s_arr.shape:
            raise ValueError("Images must have identical dimensions for pixel-by-pixel comparison.")

        diff = np.abs(c_arr.astype(int) - s_arr.astype(int)).astype(np.uint8)
        # Amplify difference for visual inspection (difference of 1 becomes 255)
        diff_amplified = np.clip(diff * 255, 0, 255).astype(np.uint8)

        mse = float(np.mean(diff.astype(float) ** 2))
        psnr = round(10.0 * math.log10((255.0 ** 2) / mse), 2) if mse > 0 else 99.0
        differing_pixels = int(np.count_nonzero(diff))

        diff_buf = io.BytesIO()
        Image.fromarray(diff_amplified).save(diff_buf, format="PNG")
        diff_b64 = base64.b64encode(diff_buf.getvalue()).decode("utf-8")

        return {
            "mse": round(mse, 6),
            "psnr_db": psnr,
            "differing_pixel_channels": differing_pixels,
            "differing_percentage": round((differing_pixels / diff.size) * 100, 3),
            "difference_map_png_base64": diff_b64
        }


steganography_service = SteganographyService()
