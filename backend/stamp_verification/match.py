"""Step 4 - Stamp matching: how well does a detected stamp match each reference stamp?

For every reference:
  1. SIFT keypoints  - distinctive little patterns (letter corners, ring edges) on both images
  2. Ratio test      - keep only matches clearly better than the 2nd-best (removes ambiguous ones)
  3. RANSAC          - find ONE geometric transform (rotation, scale, shift, perspective) that most
                       matches agree with; matches that disagree are discarded as noise
  4. Warp + overlap  - move the detected stamp onto the reference with that transform and measure
                       how much the ink overlaps (IoU). Confirms the whole shape lines up.

confidence = 0.7 * keypoint score + 0.3 * overlap score   (0 = no match, 1 = perfect)

The keypoint score counts consistent matches RELATIVE to the reference's own keypoints: two different
seals that share a word or a ring layout agree on a few percent of points, the same stamp on 15%+.
Overlap gets less weight because stamps with the same layout (two rings) overlap well even when
their text differs.
"""
from dataclasses import dataclass

import cv2
import numpy as np

from stamp_verification.features import StampFeatures
from stamp_verification.references import Reference

MIN_GOOD_MATCHES = 8      # fewer than this: can't estimate a transform reliably
FULL_FRACTION = 0.20      # consistent matches on 20% of the reference's keypoints = full keypoint score
MIN_INLIERS = 15          # below this many consistent matches the keypoint score is scaled down
_MATCHER = cv2.BFMatcher(cv2.NORM_L2)
_KERNEL = np.ones((5, 5), np.uint8)


@dataclass
class MatchScore:
    reference: str
    confidence: float
    inliers: int
    overlap: float


def _score(candidate: StampFeatures, ref: Reference) -> MatchScore:
    none = MatchScore(ref.name, 0.0, 0, 0.0)
    r = ref.features
    if candidate.descriptors is None or r.descriptors is None or len(r.keypoints) < 2 or len(candidate.keypoints) < 2:
        return none

    # 1-2. match keypoints, keep the unambiguous ones (Lowe's ratio test)
    pairs = _MATCHER.knnMatch(candidate.descriptors, r.descriptors, k=2)
    good = [m for m, n in (p for p in pairs if len(p) == 2) if m.distance < 0.75 * n.distance]
    if len(good) < MIN_GOOD_MATCHES:
        return none

    # 3. one transform that most matches agree with (RANSAC throws out the rest)
    src = np.float32([candidate.keypoints[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst = np.float32([r.keypoints[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    H, inlier_flags = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
    if H is None:
        return none
    det = np.linalg.det(H[:2, :2])
    if not 0.2 < det < 5:          # absurd stretch/flip: not a real match
        return none
    inliers = int(inlier_flags.sum())
    # Share of keypoints that line up, out of the SMALLER image's keypoints: a blurry scan has far
    # fewer keypoints than the reference, and shouldn't be punished for that
    fraction = inliers / min(len(r.keypoints), len(candidate.keypoints))
    keypoint_score = min(1.0, fraction / FULL_FRACTION) * min(1.0, inliers / MIN_INLIERS)

    # 4. put the detected stamp on top of the reference and measure ink overlap
    h, w = r.mask.shape
    warped = cv2.warpPerspective(candidate.mask, H, (w, h), flags=cv2.INTER_NEAREST)
    a, b = cv2.dilate(warped, _KERNEL) > 0, cv2.dilate(r.mask, _KERNEL) > 0
    union = np.count_nonzero(a | b)
    overlap = np.count_nonzero(a & b) / union if union else 0.0

    confidence = 0.7 * keypoint_score + 0.3 * overlap
    return MatchScore(ref.name, round(float(confidence), 3), inliers, round(float(overlap), 3))


def match_against_references(candidate: StampFeatures, references: list[Reference]) -> list[MatchScore]:
    """Scores against every reference, best first."""
    return sorted((_score(candidate, ref) for ref in references), key=lambda s: s.confidence, reverse=True)
