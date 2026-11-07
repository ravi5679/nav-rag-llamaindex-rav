import { useState } from 'react'
import type { RagType } from '../../shared/endpoints'
import { ingestApi, type IngestResponse } from './ingestApi'

const ACCEPT = '.pdf,.txt,.md,.docx,.csv' // keep in sync with backend ALLOWED
const RAG_LABEL: Record<RagType, string> = { naive: 'Naive RAG', hybrid: 'Hybrid RAG' }

export function DocumentUploadPage({ rag }: { rag: RagType }) {
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [status, setStatus] = useState<{ ok: boolean; text: string } | null>(null)

  const run = async (fn: () => Promise<IngestResponse>) => {
    setBusy(true)
    setStatus(null)
    try {
      const r = await fn()
      setStatus({ ok: true, text: `${r.message} (${r.documents_added} documents)` })
    } catch (e) {
      setStatus({ ok: false, text: e instanceof Error ? e.message : 'Request failed' })
    } finally {
      setBusy(false)
    }
  }

  return (
    <section>
      <h2>Upload a document</h2>
      <p className="muted">Allowed: {ACCEPT}. Embedding can take a while for large files.</p>
      <p className="muted">
        One document at a time: uploading a new file replaces the current one. {RAG_LABEL[rag]} keeps its own
        document, separate from the other RAG types. Your documents and indexes are deleted when you log out or
        after 60 minutes of inactivity.
      </p>
      <div className="row">
        <input type="file" accept={ACCEPT} onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        <button disabled={!file || busy} onClick={() => file && run(() => ingestApi.upload(rag, file))}>
          {busy ? 'Working…' : 'Upload'}
        </button>
      </div>
      <h3>Rebuild index</h3>
      <p className="muted">
        Re-chunks and re-embeds your current document, e.g. after changing chunk settings.
      </p>
      <button disabled={busy} onClick={() => run(() => ingestApi.reindex(rag))}>
        Reindex
      </button>
      {status && <p className={status.ok ? 'ok' : 'error'}>{status.text}</p>}
    </section>
  )
}
