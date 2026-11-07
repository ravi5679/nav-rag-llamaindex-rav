"""Response shapes of the stamp API (mirrored in frontend/src/features/stamp-verification/types.ts)."""
from typing import Literal

from pydantic import BaseModel

Status = Literal["Matched", "Unknown Stamp", "No Stamp"]


class Candidate(BaseModel):
    reference: str
    confidence: float


class DetectedStamp(BaseModel):
    page: int
    bbox: list[int]                    # x0, y0, x1, y1 in page pixels at the render DPI
    shape: str                         # round | rectangular | other
    detection_score: float             # how stamp-like the region looks (0..1)
    stamp_image: str                   # extracted stamp as a PNG data URI
    matched_reference: str | None      # reference stamp id, None if unknown
    confidence: float                  # match confidence (0..1)
    status: Literal["Matched", "Unknown Stamp"]
    top_candidates: list[Candidate]


class StampVerification(BaseModel):
    file_name: str
    pages_checked: int
    stamp_present: Literal["Yes", "No"]
    status: Status                     # final status for the whole document
    matched_reference: str | None      # best matched reference (if status is Matched)
    confidence: float                  # confidence of the best stamp
    stamps: list[DetectedStamp]


class ReferenceStamp(BaseModel):
    name: str
    image: str                         # PNG data URI thumbnail
