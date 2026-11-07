import { useCallback, useState } from 'react'
import type { RagType } from '../../../shared/endpoints'
import { ragApi } from '../services/ragApi'
import type { QueryResponse } from '../types'

export interface ChatTurn {
  id: number
  question: string
  response?: QueryResponse
  error?: string
}

export function useRagQuery(rag: RagType) {
  const [turns, setTurns] = useState<ChatTurn[]>([])
  const [loading, setLoading] = useState(false)

  const ask = useCallback(async (question: string, topK: number | null) => {
    const id = Date.now()
    setTurns((t) => [...t, { id, question }])
    setLoading(true)
    try {
      const response = await ragApi.query(rag, { question, top_k: topK })
      setTurns((t) => t.map((x) => (x.id === id ? { ...x, response } : x)))
    } catch (e) {
      const error = e instanceof Error ? e.message : 'Request failed'
      setTurns((t) => t.map((x) => (x.id === id ? { ...x, error } : x)))
    } finally {
      setLoading(false)
    }
  }, [rag])

  return { turns, loading, ask }
}
