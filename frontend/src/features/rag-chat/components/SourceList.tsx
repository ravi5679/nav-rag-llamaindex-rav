import type { SourceNode } from '../types'

export function SourceList({ sources }: { sources: SourceNode[] }) {
  if (sources.length === 0) return null
  return (
    <details className="sources">
      <summary>
        {sources.length} source{sources.length > 1 ? 's' : ''}
      </summary>
      <ul>
        {sources.map((s, i) => (
          <li key={i}>
            <strong>{s.file_name ?? 'unknown file'}</strong>
            {s.score != null && <span className="score"> · score {s.score.toFixed(2)}</span>}
            <p>{s.text}</p>
          </li>
        ))}
      </ul>
    </details>
  )
}
