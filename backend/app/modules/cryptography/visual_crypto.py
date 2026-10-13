import io
import base64
import secrets
import numpy as np
from PIL import Image
from typing import Dict, Any, Tuple


class VisualCryptographyService:
    """
    2-out-of-2 Visual Secret Sharing (Naor & Shamir).
    Each secret pixel is mapped to a 2x2 subpixel block in each share.
    Share 1 alone: pure random entropy (50% black).
    Share 2 alone: pure random entropy (50% black).
    Overlay (Share 1 + Share 2):
      - Secret White pixel -> 2 black subpixels (50% gray)
      - Secret Black pixel -> 4 black subpixels (100% black)
    """

    # 2x2 subpixel pattern representations (2 black, 2 white subpixels each)
    # 0 = Black, 255 = White
    PATTERNS = [
        # Pattern 0: top row black, bottom row white
        np.array([[0, 0], [255, 255]], dtype=np.uint8),
        # Pattern 1: top row white, bottom row black
        np.array([[255, 255], [0, 0]], dtype=np.uint8),
        # Pattern 2: left col black, right col white
        np.array([[0, 255], [0, 255]], dtype=np.uint8),
        # Pattern 3: left col white, right col black
        np.array([[255, 0], [255, 0]], dtype=np.uint8),
        # Pattern 4: diagonal
        np.array([[0, 255], [255, 0]], dtype=np.uint8),
        # Pattern 5: anti-diagonal
        np.array([[255, 0], [0, 255]], dtype=np.uint8),
    ]

    # Inverted patterns (complement)
    COMPLEMENTS = [
        np.array([[255, 255], [0, 0]], dtype=np.uint8),
        np.array([[0, 0], [255, 255]], dtype=np.uint8),
        np.array([[255, 0], [255, 0]], dtype=np.uint8),
        np.array([[0, 255], [0, 255]], dtype=np.uint8),
        np.array([[255, 0], [0, 255]], dtype=np.uint8),
        np.array([[0, 255], [255, 0]], dtype=np.uint8),
    ]

    def threshold_image(self, img_bytes: bytes, threshold: int = 128) -> Tuple[np.ndarray, int, int]:
        """Converts arbitrary input image into binary black & white matrix (0 or 255)."""
        pil_img = Image.open(io.BytesIO(img_bytes)).convert("L")
        
        # Max dimension 256 for educational responsiveness
        pil_img.thumbnail((256, 256))
        arr = np.array(pil_img)
        
        # Threshold: < threshold is Black (0), >= threshold is White (255)
        binary = np.where(arr < threshold, 0, 255).astype(np.uint8)
        h, w = binary.shape
        return binary, h, w

    def split_secret_image(self, img_bytes: bytes, threshold: int = 128) -> Dict[str, Any]:
        """
        Splits secret image into Share 1 and Share 2 using 2x2 subpixel visual secret sharing.
        """
        binary, h, w = self.threshold_image(img_bytes, threshold)

        # Output shares will be 2h x 2w
        share1 = np.zeros((h * 2, w * 2), dtype=np.uint8)
        share2 = np.zeros((h * 2, w * 2), dtype=np.uint8)

        # Cryptographically secure random selection of patterns
        rng = secrets.SystemRandom()

        for y in range(h):
            for x in range(w):
                is_black = (binary[y, x] == 0)
                pat_idx = rng.randint(0, len(self.PATTERNS) - 1)
                p1 = self.PATTERNS[pat_idx]

                if is_black:
                    # For Black secret pixel: share 2 gets complementary pattern
                    p2 = self.COMPLEMENTS[pat_idx]
                else:
                    # For White secret pixel: share 2 gets identical pattern
                    p2 = self.PATTERNS[pat_idx]

                y2, x2 = y * 2, x * 2
                share1[y2:y2 + 2, x2:x2 + 2] = p1
                share2[y2:y2 + 2, x2:x2 + 2] = p2

        # Convert matrices to PNG base64
        share1_b64 = self._mat_to_png_base64(share1)
        share2_b64 = self._mat_to_png_base64(share2)

        # Also precompute the direct physical overlay (minimum intensity = optical stacking)
        overlay = np.minimum(share1, share2)
        overlay_b64 = self._mat_to_png_base64(overlay)

        return {
            "original_width": w,
            "original_height": h,
            "share_width": w * 2,
            "share_height": h * 2,
            "expansion_factor": "2x2 subpixels (4x area expansion)",
            "contrast_ratio": "50% vs 100% extinction",
            "share1_png_base64": share1_b64,
            "share2_png_base64": share2_b64,
            "overlay_preview_base64": overlay_b64
        }

    def reconstruct_from_shares(self, share1_bytes: bytes, share2_bytes: bytes) -> Dict[str, Any]:
        """
        Reconstructs the secret image by physically superimposing two shares.
        Optical stacking corresponds to minimum intensity: black (0) blocks light.
        """
        s1 = Image.open(io.BytesIO(share1_bytes)).convert("L")
        s2 = Image.open(io.BytesIO(share2_bytes)).convert("L")

        arr1 = np.array(s1)
        arr2 = np.array(s2)

        if arr1.shape != arr2.shape:
            # Resize share 2 to share 1 if dimensions differ
            s2 = s2.resize((arr1.shape[1], arr1.shape[0]))
            arr2 = np.array(s2)

        # Optical overlay: stacking slides
        reconstructed = np.minimum(arr1, arr2)
        reconstructed_b64 = self._mat_to_png_base64(reconstructed)

        return {
            "width": arr1.shape[1],
            "height": arr1.shape[0],
            "reconstructed_png_base64": reconstructed_b64,
            "explanation": (
                "Superimposing both shares superimposes light paths. "
                "Original white pixels appear with 50% transmission (medium gray), "
                "while original black pixels appear with 0% transmission (black)."
            )
        }

    def _mat_to_png_base64(self, mat: np.ndarray) -> str:
        img = Image.fromarray(mat)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")


visual_crypto_service = VisualCryptographyService()
