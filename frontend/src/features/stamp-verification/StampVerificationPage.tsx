import { useEffect, useState } from 'react'
import { stampApi } from './stampApi'
import type { DetectedStamp, ReferenceStamp, StampStatus, StampVerification } from './types'
import './stamp-verification.css'

const STATUS_CLASS: Record<StampStatus, string> = {
  Matched: 'matched',
  'Unknown Stamp': 'unknown',
  'No Stamp': 'none',
}

const pct = (x: number) => `${Math.round(x * 100)}%`

function ConfidenceBar({ value }: { value: number }) {
  return (
    <div className="conf" role="meter" aria-valuemin={0} aria-valuemax={1} aria-valuenow={value} aria-label="Match confidence">
      <div className="conf-fill" style={{ width: pct(value) }} />
      <span>{pct(value)}</span>
    </div>
  )
}

function StampCard({ stamp, index, refImages }: { stamp: DetectedStamp; index: number; refImages: Map<string, string> }) {
  const refImage = stamp.matched_reference ? refImages.get(stamp.matched_reference) : undefined
  return (
    <article className="stamp-card">
      <header>
        <h3>Stamp {index + 1}</h3>
        <span className={`badge ${STATUS_CLASS[stamp.status]}`}>{stamp.status}</span>
      </header>

      <div className="stamp-compare">
        <figure>
          <img src={stamp.stamp_image} alt={`Stamp ${index + 1} extracted from page ${stamp.page}`} />
          <figcaption>Extracted · page {stamp.page}</figcaption>
        </figure>
        <figure className={refImage ? '' : 'empty'}>
          {refImage ? <img src={refImage} alt={`Reference ${stamp.matched_reference}`} /> : <span>No matching reference</span>}
          <figcaption>{stamp.matched_reference ?? 'Unknown Stamp'}</figcaption>
        </figure>
      </div>

      <dl className="stamp-facts">
        <dt>Match confidence</dt>
        <dd><ConfidenceBar value={stamp.confidence} /></dd>
        <dt>Detection</dt>
        <dd>{stamp.shape} stamp · {pct(stamp.detection_score)} stamp-like</dd>
        <dt>Closest references</dt>
        <dd>
          <ol className="candidates">
            {stamp.top_candidates.map((c) => (
              <li key={c.reference}><code>{c.reference}</code> {pct(c.confidence)}</li>
            ))}
          </ol>
        </dd>
      </dl>
    </article>
  )
}

export function StampVerificationPage() {
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<StampVerification | null>(null)
  const [references, setReferences] = useState<ReferenceStamp[]>([])

  useEffect(() => {
    stampApi.references().then(setReferences).catch(() => setReferences([]))
  }, [])

  const refImages = new Map(references.map((r) => [r.name, r.image]))

  const verify = async () => {
    if (!file) return
    setBusy(true)
    setError('')
    setResult(null)
    try {
      setResult(await stampApi.verify(file))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Verification failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="stamp-page">
      <div className="stamp-main">
        <section className="stamp-panel">
          <h2>Verify a PDF</h2>
          <p className="muted">
            Upload a PDF; every page is checked for official stamps, and each stamp is compared with the reference
            stamps. Up to 20 pages / 20 MB.
          </p>
          <div className="row">
            <input
              type="file"
              accept="application/pdf,.pdf"
              onChange={(e) => {
                setFile(e.target.files?.[0] ?? null)
                setResult(null)
                setError('')
              }}
            />
            <button disabled={!file || busy} onClick={verify}>
              {busy ? 'Checking…' : 'Verify stamps'}
            </button>
          </div>
          {error && <p className="error" role="alert">{error}</p>}
        </section>

        {result && (
          <section className="stamp-panel" aria-live="polite">
            <div className="summary">
              <div>
                <h2>{result.file_name}</h2>
                <p className="muted">{result.pages_checked} page{result.pages_checked > 1 ? 's' : ''} checked</p>
              </div>
              <span className={`badge big ${STATUS_CLASS[result.status]}`}>{result.status}</span>
            </div>
            <dl className="summary-facts">
              <div><dt>Stamp present</dt><dd>{result.stamp_present}</dd></div>
              <div><dt>Matched reference</dt><dd>{result.matched_reference ?? '–'}</dd></div>
              <div><dt>Confidence</dt><dd>{result.stamps.length ? pct(result.confidence) : '–'}</dd></div>
              <div><dt>Stamps found</dt><dd>{result.stamps.length}</dd></div>
            </dl>
          </section>
        )}

        {result?.stamps.map((s, i) => <StampCard key={i} stamp={s} index={i} refImages={refImages} />)}
      </div>

      <aside className="stamp-panel stamp-refs" aria-label="Reference stamps">
        <h2>Reference stamps</h2>
        <p className="muted">
          {references.length} stamp{references.length === 1 ? '' : 's'} in <code>backend/stamps/</code>. Add an image
          there to recognise a new stamp.
        </p>
        <ul>
          {references.map((r) => (
            <li key={r.name} className={result?.stamps.some((s) => s.matched_reference === r.name) ? 'hit' : ''}>
              <img src={r.image} alt="" />
              <code>{r.name}</code>
            </li>
          ))}
        </ul>
      </aside>
    </div>
  )
}
