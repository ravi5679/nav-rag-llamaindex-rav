import type { ChatTurn } from '../hooks/useRagQuery'
import { SourceList } from './SourceList'

export function ChatMessage({ turn }: { turn: ChatTurn }) {
  return (
    <div className="turn">
      <div className="bubble user">{turn.question}</div>
      <div className="bubble bot">
        {turn.error ? (
          <span className="error">{turn.error}</span>
        ) : turn.response ? (
          <>
            <p>{turn.response.answer}</p>
            <SourceList sources={turn.response.sources} />
          </>
        ) : (
          <span className="muted">Thinking…</span>
        )}
      </div>
    </div>
  )
}
