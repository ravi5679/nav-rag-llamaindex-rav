import { useState, type ReactNode } from 'react'

// A tiny Python/bash highlighter: enough for teaching snippets, no extra dependency.
// One regex with named groups; anything that doesn't match is left as plain text.
const TOKEN = new RegExp(
  [
    String.raw`(?<comment>#[^\n]*)`,
    String.raw`(?<string>[rfb]?"""[\s\S]*?"""|[rfb]?"(?:\\.|[^"\\\n])*"|[rfb]?'(?:\\.|[^'\\\n])*')`,
    String.raw`(?<keyword>\b(?:import|from|as|def|return|if|else|elif|for|in|not|and|or|is|None|True|False|with|class|try|except|finally|raise|lambda|print)\b)`,
    String.raw`(?<number>\b\d+(?:\.\d+)?\b)`,
    String.raw`(?<call>\b[A-Za-z_]\w*(?=\())`,
  ].join('|'),
  'g',
)

function highlight(code: string): ReactNode[] {
  const out: ReactNode[] = []
  let last = 0
  for (const m of code.matchAll(TOKEN)) {
    const kind = Object.entries(m.groups ?? {}).find(([, v]) => v !== undefined)?.[0]
    if (m.index > last) out.push(code.slice(last, m.index))
    out.push(<span key={m.index} className={`tok-${kind}`}>{m[0]}</span>)
    last = m.index + m[0].length
  }
  if (last < code.length) out.push(code.slice(last))
  return out
}

export function CodeBlock({ code, lang }: { code: string; lang: string }) {
  const [copied, setCopied] = useState(false)

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      /* clipboard blocked (e.g. insecure context): user can still select the text */
    }
  }

  return (
    <div className="code-block">
      <div className="code-bar">
        <span>{lang}</span>
        <button type="button" className="code-copy" onClick={copy} aria-live="polite">
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <pre>
        <code>{highlight(code)}</code>
      </pre>
    </div>
  )
}
