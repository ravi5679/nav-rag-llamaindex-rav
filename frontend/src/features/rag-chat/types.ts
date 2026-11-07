// Mirrors backend/common/schemas.py
export interface QueryRequest {
  question: string
  top_k?: number | null
}

export interface SourceNode {
  file_name: string | null
  score: number | null
  text: string
}

export interface QueryResponse {
  answer: string
  sources: SourceNode[]
}
