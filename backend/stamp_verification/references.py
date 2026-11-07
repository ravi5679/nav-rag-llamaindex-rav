"""Step 3 - Reference stamps: load backend/stamps/*, precompute their features once.

One image per reference stamp; the file name (without extension) is the stamp id, e.g.
`finance_dept_seal.png` -> "finance_dept_seal". Adding/removing files is picked up automatically.
"""
import logging
import threading
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from stamp_verification.detect import dark_mask, ink_mask, ink_strength
from stamp_verification.features import StampFeatures, compute_features, to_png_base64, trim_to_ink

logger = logging.getLogger(__name__)
IMAGE_TYPES = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tif", ".tiff"}


@dataclass
class Reference:
    name: str
    image: np.ndarray        # BGR, trimmed to the ink
    features: StampFeatures


_cache: dict = {"signature": None, "refs": []}
_lock = threading.Lock()


def _load_one(path: Path) -> Reference | None:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        logger.warning("Skipping unreadable reference stamp %s", path.name)
        return None
    mask = ink_mask(image)
    colour = np.count_nonzero(mask) >= 0.01 * mask.size   # hardly any colour: treat as a black stamp
    if not colour:
        mask = dark_mask(image)
    image, _ = trim_to_ink(image, mask)
    return Reference(path.stem, image, compute_features(ink_strength(image, colour)))


def load_references(folder: str) -> list[Reference]:
    """All reference stamps in `folder`, recomputed only when the files change."""
    root = Path(folder)
    files = sorted(p for p in root.glob("*") if p.suffix.lower() in IMAGE_TYPES) if root.exists() else []
    signature = tuple((p.name, p.stat().st_mtime_ns) for p in files)
    with _lock:
        if signature != _cache["signature"]:
            _cache["refs"] = [r for r in (_load_one(p) for p in files) if r is not None]
            _cache["signature"] = signature
            logger.info("Loaded %d reference stamps from %s", len(_cache["refs"]), root)
        return _cache["refs"]


def list_references(folder: str) -> list[dict]:
    return [{"name": r.name, "image": to_png_base64(r.image, max_side=160)} for r in load_references(folder)]
