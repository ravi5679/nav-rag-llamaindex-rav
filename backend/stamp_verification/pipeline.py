"""Step 5 - Run the whole check on one PDF and decide: Matched / Unknown Stamp / No Stamp.

  render pages -> detect stamps -> match each stamp against the references -> verify
"""
import logging

from common.config import get_config
from stamp_verification.detect import detect_stamps, ink_strength
from stamp_verification.features import compute_features, to_png_base64
from stamp_verification.match import match_against_references
from stamp_verification.pdf_to_images import render_pages
from stamp_verification.references import load_references

logger = logging.getLogger(__name__)

MATCHED, UNKNOWN, NO_STAMP = "Matched", "Unknown Stamp", "No Stamp"


def _decide(scores: list) -> tuple[str | None, float, str]:
    """Matched only if the best reference is confident enough AND clearly ahead of the runner-up."""
    if not scores:
        return None, 0.0, UNKNOWN
    best = scores[0]
    second = scores[1].confidence if len(scores) > 1 else 0.0
    if best.confidence >= get_config("stamps.match_threshold") and best.confidence - second >= get_config("stamps.match_margin"):
        return best.reference, best.confidence, MATCHED
    return None, best.confidence, UNKNOWN


def verify_pdf(pdf_bytes: bytes, file_name: str) -> dict:
    references = load_references(get_config("stamps.references_dir"))
    pages = render_pages(pdf_bytes, get_config("stamps.render_dpi"), get_config("stamps.max_pages"))

    stamps = []
    for page_no, page in enumerate(pages, start=1):
        for cand in detect_stamps(page):                                      # detection
            features = compute_features(ink_strength(cand.crop, cand.colour))
            scores = match_against_references(features, references)           # matching
            reference, confidence, status = _decide(scores)                    # verification
            stamps.append({
                "page": page_no,
                "bbox": list(cand.bbox),
                "shape": cand.shape,
                "detection_score": cand.score,
                "stamp_image": to_png_base64(cand.crop),
                "matched_reference": reference,
                "confidence": confidence,
                "status": status,
                "top_candidates": [{"reference": s.reference, "confidence": s.confidence} for s in scores[:3]],
            })

    if any(s["status"] == MATCHED for s in stamps):
        status = MATCHED
    elif stamps:
        status = UNKNOWN
    else:
        status = NO_STAMP
    best = max(stamps, key=lambda s: s["confidence"], default=None)
    logger.info("%s: %d page(s), %d stamp(s), status %s", file_name, len(pages), len(stamps), status)
    return {
        "file_name": file_name,
        "pages_checked": len(pages),
        "stamp_present": "Yes" if stamps else "No",
        "status": status,
        "matched_reference": best["matched_reference"] if best and status == MATCHED else None,
        "confidence": best["confidence"] if best else 0.0,
        "stamps": stamps,
    }
