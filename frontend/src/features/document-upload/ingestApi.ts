import { ragEndpoints, type RagType } from '../../shared/endpoints'
import { http } from '../../shared/httpService'

export interface IngestResponse {
  message: string
  documents_added: number
}

export const ingestApi = {
  upload: (rag: RagType, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return http.postForm<IngestResponse>(ragEndpoints(rag).ingest, form)
  },
  reindex: (rag: RagType) => http.post<IngestResponse>(ragEndpoints(rag).reindex),
}
