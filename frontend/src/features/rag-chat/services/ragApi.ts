import { ragEndpoints, type RagType } from '../../../shared/endpoints'
import { http } from '../../../shared/httpService'
import type { QueryRequest, QueryResponse } from '../types'

export const ragApi = {
  query: (rag: RagType, body: QueryRequest) => http.postJson<QueryResponse>(ragEndpoints(rag).query, body),
}
