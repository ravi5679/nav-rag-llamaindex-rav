"""Shared image preparation for references and detected stamps, so both are compared the same way."""
import base64
from dataclasses import dataclass

import cv2
import numpy as np

SIZE = 400   # both sides are scaled so their longest side is SIZE pixels before comparing
_SIFT = cv2.SIFT_create(nfeatures=1500)


@dataclass
class StampFeatures:
    mask: np.ndarray           # 255 = ink, scaled to SIZE
    keypoints: tuple           # SIFT keypoints
    descriptors: np.ndarray | None


def trim_to_ink(image: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Cut away the empty margin around the ink."""
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return image, mask
    return image[ys.min():ys.max() + 1, xs.min():xs.max() + 1], mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def compute_features(strength: np.ndarray) -> StampFeatures:
    """Find SIFT keypoints on an ink-strength image (see detect.ink_strength), scaled to SIZE.

    We compare INK, not raw colours, so black text printed over a stamp, paper tint or a different
    scan colour matter much less. Faded ink is stretched to full contrast first.
    """
    h, w = strength.shape
    scale = SIZE / max(h, w)
    strength = cv2.resize(strength, (max(1, round(w * scale)), max(1, round(h * scale))), interpolation=cv2.INTER_AREA)
    top = np.percentile(strength, 99.5)
    if top > 0:
        strength = np.clip(strength.astype(np.float32) * (255.0 / top), 0, 255).astype(np.uint8)
    # Ink mask for the overlap check: Otsu picks the ink/paper cut-off from this image itself
    _, mask = cv2.threshold(strength, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))   # drop single-pixel noise
    # SIFT runs on the CLEAN mask (not the raw ink), blurred the same way for every image: scan
    # noise doesn't create junk keypoints, and crisp reference strokes look like blurry scanned ones
    ink_image = cv2.GaussianBlur(255 - mask, (5, 5), 0)
    keypoints, descriptors = _SIFT.detectAndCompute(ink_image, None)
    return StampFeatures(mask, keypoints, descriptors)


def to_png_base64(image: np.ndarray, max_side: int = 360) -> str:
    """Encode an image as a small PNG data URI for the JSON response."""
    h, w = image.shape[:2]
    if max(h, w) > max_side:
        s = max_side / max(h, w)
        image = cv2.resize(image, (round(w * s), round(h * s)), interpolation=cv2.INTER_AREA)
    ok, png = cv2.imencode(".png", image)
    return "data:image/png;base64," + base64.b64encode(png.tobytes()).decode() if ok else ""
