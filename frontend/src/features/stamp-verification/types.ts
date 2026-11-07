// Mirrors backend/stamp_verification/schemas.py
export type StampStatus = 'Matched' | 'Unknown Stamp' | 'No Stamp'

export interface StampCandidate {
  reference: string
  confidence: number
}

export interface DetectedStamp {
  page: number
  bbox: number[]
  shape: string
  detection_score: number
  stamp_image: string // PNG data URI
  matched_reference: string | null
  confidence: number
  status: 'Matched' | 'Unknown Stamp'
  top_candidates: StampCandidate[]
}

export interface StampVerification {
  file_name: string
  pages_checked: number
  stamp_present: 'Yes' | 'No'
  status: StampStatus
  matched_reference: string | null
  confidence: number
  stamps: DetectedStamp[]
}

export interface ReferenceStamp {
  name: string
  image: string // PNG data URI
}
