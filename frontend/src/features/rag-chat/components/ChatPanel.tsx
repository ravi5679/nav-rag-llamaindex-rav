import { useEffect, useRef } from 'react'
import type { RagType } from '../../../shared/endpoints'
import { useRagQuery } from '../hooks/useRagQuery'
import { ChatMessage } from './ChatMessage'
import { QuestionInput } from './QuestionInput'

const SEARCH_LABEL: Record<RagType, string> = {
  naive: 'Vector search',
  hybrid: 'Keyword (BM25) + vector search, fused by rank',
}

/** Left panel: scrollable message list with the question box anchored below it. */
export function ChatPanel({ rag }: { rag: RagType }) {
  const { turns, loading, ask } = useRagQuery(rag)
  const listRef = useRef<HTMLDivElement>(null)

  // Scroll the message list (not the page) to the newest message.
  // Only runs when turns change, so the user can scroll up freely in between.
  useEffect(() => {
    const el = listRef.current
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }, [turns])

  return (
    <section className="panel chat-panel" aria-label="Chat">
      <header className="panel-header">
        <h2>Ask your documents</h2>
        <p className="muted panel-sub">{SEARCH_LABEL[rag]}</p>
      </header>

      <div className="chat-messages" ref={listRef} role="log" aria-live="polite">
        {turns.length === 0 ? (
          <p className="chat-empty muted">
            Upload a document first, then ask a question about it here.
          </p>
        ) : (
          turns.map((t) => <ChatMessage key={t.id} turn={t} />)
        )}
      </div>

      <QuestionInput disabled={loading} onSubmit={ask} />
    </section>
  )
}
