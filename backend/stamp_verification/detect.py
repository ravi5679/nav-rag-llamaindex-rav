"""Step 2 - Stamp detection: find stamp-like regions on a page image (OpenCV).

Idea: official stamps are usually printed in coloured ink (blue, red, purple, green), while body
text is black. So we
  1. keep only strongly coloured pixels (HSV saturation) -> "ink mask"
  2. close small gaps so a stamp's letters and rings merge into one blob (morphology)
  3. take each blob's outline (contours) and keep the ones that look like a stamp:
     big enough, not too long/thin, partly filled with ink, round or rectangular.
Black stamps are not detected by the colour step; a round-outline fallback catches round ones.
"""
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class Candidate:
    bbox: tuple[int, int, int, int]   # x0, y0, x1, y1 in page pixels
    crop: np.ndarray                  # BGR image of the stamp region
    colour: bool                      # coloured ink (True) or black ink (False)
    score: float                      # 0..1: how stamp-like the region looks
    shape: str                        # "round" | "rectangular" | "other"


# Faded ink and JPEG-compressed scans lose a lot of colour, so the cut-off is fairly low.
# Plain paper (even slightly yellowed) and black text stay well below it.
MIN_SATURATION = 40


def ink_strength(bgr: np.ndarray, colour: bool) -> np.ndarray:
    """0..255 per pixel: how much 'stamp ink' it holds.

    Coloured stamps: the HSV saturation (how colourful), which is ~0 for black text and white paper,
    so text printed over a stamp disappears. Black stamps: darkness.
    """
    if colour:
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        return np.where(hsv[:, :, 2] >= 50, hsv[:, :, 1], 0).astype(np.uint8)
    return (255 - cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)).astype(np.uint8)


def ink_mask(bgr: np.ndarray) -> np.ndarray:
    """255 where the pixel is coloured ink (not white paper, not black/grey text)."""
    return np.where(ink_strength(bgr, colour=True) >= MIN_SATURATION, 255, 0).astype(np.uint8)


def dark_mask(bgr: np.ndarray) -> np.ndarray:
    """255 where the pixel is dark (black ink), used for the black-stamp fallback."""
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    return np.where(gray < 110, 255, 0).astype(np.uint8)


def _shape_of(contour: np.ndarray) -> tuple[str, float]:
    """Classify an outline as round / rectangular and return how regular it is (0..1)."""
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)
    if perimeter == 0 or area == 0:
        return "other", 0.0
    circularity = 4 * np.pi * area / perimeter ** 2           # 1.0 = perfect circle
    (_, _), (w, h), _ = cv2.minAreaRect(contour)
    rectangularity = area / (w * h) if w * h else 0          # 1.0 = perfect rectangle
    if circularity >= 0.80:
        return "round", min(1.0, circularity)
    if rectangularity >= 0.85:
        return "rectangular", rectangularity
    return "other", max(circularity, rectangularity) * 0.7


def _candidates_from_mask(bgr: np.ndarray, mask: np.ndarray, colour: bool) -> list[Candidate]:
    h, w = mask.shape
    unit = max(h, w)
    # Merge each stamp's strokes into one solid blob. Kernel ~1.5% of the page size.
    k = max(5, int(unit * 0.015)) | 1
    blobs = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    blobs = cv2.dilate(blobs, np.ones((3, 3), np.uint8), iterations=2)
    contours, _ = cv2.findContours(blobs, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    found = []
    for c in contours:
        x, y, bw, bh = cv2.boundingRect(c)
        side, long_side = min(bw, bh), max(bw, bh)
        if side < unit * 0.04 or long_side > unit * 0.6:   # too small (a word) or too big (a banner)
            continue
        if long_side / side > 3.5:                          # long thin strokes: underlines, signatures
            continue
        shape, regularity = _shape_of(cv2.convexHull(c))
        if not colour and shape != "round":                 # black fallback: only clear round seals
            continue
        density = float(np.count_nonzero(mask[y:y + bh, x:x + bw])) / (bw * bh)
        if not 0.03 <= density <= 0.65:                    # empty box, or a solid coloured block
            continue

        size_score = min(1.0, side / (unit * 0.08))
        density_score = 1.0 - abs(density - 0.25) / 0.4
        score = (0.5 * regularity + 0.25 * size_score + 0.25 * max(0.0, density_score)) * (1.0 if colour else 0.8)

        pad = int(side * 0.06)
        x0, y0 = max(0, x - pad), max(0, y - pad)
        x1, y1 = min(w, x + bw + pad), min(h, y + bh + pad)
        found.append(Candidate((x0, y0, x1, y1), bgr[y0:y1, x0:x1].copy(), colour, round(float(score), 3), shape))
    return found


def detect_stamps(page: np.ndarray, min_score: float = 0.35) -> list[Candidate]:
    """All stamp-like regions on a page, most stamp-like first."""
    candidates = _candidates_from_mask(page, ink_mask(page), colour=True)
    if not candidates:   # nothing coloured: try round black seals
        candidates = _candidates_from_mask(page, dark_mask(page), colour=False)
    return sorted((c for c in candidates if c.score >= min_score), key=lambda c: c.score, reverse=True)
