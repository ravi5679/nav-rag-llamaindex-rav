import { useEffect, useRef, useState } from 'react'

interface Props {
  disabled: boolean
  onSubmit: (question: string, topK: number | null) => void
}

export function QuestionInput({ disabled, onSubmit }: Props) {
  const [question, setQuestion] = useState('')
  const [topK, setTopK] = useState(4)
  const inputRef = useRef<HTMLInputElement>(null)

  // A disabled input loses focus; give it back when the answer arrives
  useEffect(() => {
    if (!disabled) inputRef.current?.focus()
  }, [disabled])

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    const q = question.trim()
    if (q.length < 3) return
    onSubmit(q, topK)
    setQuestion('')
  }

  return (
    <form className="question-form" onSubmit={submit}>
      <input
        ref={inputRef}
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask about your documents..."
        maxLength={2000}
        disabled={disabled}
      />
      <label title="Number of chunks to retrieve">
        top_k
        <input
          type="number"
          min={1}
          max={20}
          value={topK}
          onChange={(e) => setTopK(Number(e.target.value))}
        />
      </label>
      <button type="submit" disabled={disabled || question.trim().length < 3}>
        {disabled ? 'Thinking…' : 'Ask'}
      </button>
    </form>
  )
}
