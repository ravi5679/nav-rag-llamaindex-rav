import flowGif from '../../assets/stamp-verification-flow.gif'
import { StepList } from './archShared'
import type { Step } from './archSteps'
import './rag-architecture.css'

// Keep in sync with backend/stamp_verification/ and scripts/make_stamp_flow_gif.py
const detectSteps: Step[] = [
  { name: 'Upload PDF', what: 'Sends the PDF with the login token. Only .pdf, max 20 MB and 20 pages; processed in memory, never stored.', code: 'stamp_verification/routes.py' },
  { name: 'Render pages', what: 'PyMuPDF turns every page into an image (200 dpi), so scans, pasted images and vector stamps are all caught.', code: 'stamp_verification/pdf_to_images.py' },
  { name: 'Ink mask', what: 'Keeps only coloured ink (HSV saturation). Black text and white paper drop out, even text printed over a stamp.', code: 'stamp_verification/detect.py' },
  { name: 'Find stamps', what: 'Merges strokes into blobs, keeps round / rectangular shapes of the right size and ink density, and scores each one. Black round seals are a fallback.', code: 'stamp_verification/detect.py' },
]

const verifySteps: Step[] = [
  { name: 'Features', what: 'Each crop is scaled to the same size, its ink cleaned, and SIFT keypoints found: the references are prepared the same way.', code: 'stamp_verification/features.py' },
  { name: 'Match', what: 'Keypoints are compared with every reference in backend/stamps/; Lowe’s ratio test drops ambiguous pairs.', code: 'stamp_verification/match.py' },
  { name: 'Align + overlap', what: 'RANSAC finds one rotation / scale / shift most matches agree on; the warped ink overlap confirms the whole shape.', code: 'stamp_verification/match.py' },
  { name: 'Decide', what: 'confidence = 0.7 · keypoints + 0.3 · overlap. Matched only if ≥ 0.55 and 0.10 ahead of the runner-up; otherwise Unknown Stamp. No stamps found: No Stamp.', code: 'stamp_verification/pipeline.py' },
]

export function StampArchitecturePage() {
  return (
    <div className="arch-page">
      <h2 className="arch-heading">Stamp verification flow</h2>
      <section className="arch-card arch-flow">
        <img
          src={flowGif}
          alt="Animated stamp verification flow. Detection: Upload PDF, Render pages, Ink mask, Find stamps. Verification: Features, Match against the reference stamps, Align with RANSAC and overlap, Decide Matched, Unknown Stamp or No Stamp."
          width={1200}
          height={410}
        />
      </section>

      <div className="arch-grid">
        <StepList title="1 · Detection" endpoint="POST /api/v1/stamps/verify" steps={detectSteps} tone="ingest" />
        <StepList title="2 · Verification" endpoint="runs per detected stamp" steps={verifySteps} tone="query" />
      </div>

      <p className="muted arch-note">
        This uses classic computer vision (OpenCV, SIFT), not a trained model. Reference stamps are the images in{' '}
        <code>backend/stamps/</code>: add or remove a file and it is picked up automatically. A match means the stamp{' '}
        <strong>looks the same</strong> as a reference, not that the document is proven authentic.
      </p>
    </div>
  )
}
