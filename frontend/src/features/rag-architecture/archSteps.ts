// Step data shared by the Naive and Hybrid architecture pages.
import type { RagType } from '../../shared/endpoints'

export interface Step {
  name: string
  what: string
  code: string // file in backend/
}

/** Ingestion is identical for every RAG type (backend/common/index_store.py). */
export const ingestSteps = (rag: RagType): Step[] => [
  { name: 'Upload', what: 'Replaces this RAG type’s previous file in the session, then reads it into Documents (one per PDF page).', code: 'rag_steps/load_documents.py' },
  { name: 'Chunk', what: 'SentenceSplitter: 512-token chunks, 50 tokens overlap.', code: 'rag_steps/chunk_documents.py' },
  { name: 'Embedding', what: 'OpenAI text-embedding-3-small: one vector per chunk.', code: 'rag_steps/embed_chunks.py' },
  { name: 'Vector DB + indexing', what: `Chunk text + vectors in LanceDB; index + chunks saved next to it (storage/sessions/<id>/${rag}/).`, code: 'rag_steps/vector_index.py' },
]

export const sessionSteps: Step[] = [
  { name: 'Login / Sign up', what: 'Email + password; passwords are stored only as scrypt hashes.', code: 'common/auth.py' },
  { name: 'Token + session id', what: 'The server returns both. Every request sends Authorization: Bearer + X-Session-Id; a session id that isn’t this token’s is rejected.', code: 'common/auth.py' },
  { name: 'Upload & ask', what: 'Each request refreshes last_active. One file per RAG type; a new upload replaces the old one.', code: 'common/session.py' },
  { name: 'Session ends', what: 'Logout ends it now. Otherwise a cleanup job (every 5 min, and at startup) ends it after 60 min idle or 24 h.', code: 'main.py' },
  { name: 'Data deleted', what: 'Files, LanceDB vectors, saved indexes and in-memory copies of every RAG type. The token stops working; the account stays.', code: 'common/index_store.py' },
]

export const dataLocations = (rag: RagType) => [
  { path: `data/sessions/<id>/${rag}/`, what: 'The uploaded file (one at a time)', lifetime: 'Session' },
  { path: `storage/sessions/<id>/${rag}/lancedb/`, what: 'Chunk text + vectors (vector + full-text search)', lifetime: 'Session' },
  { path: `storage/sessions/<id>/${rag}/index/`, what: 'Saved index: docstore + metadata', lifetime: 'Session' },
  { path: 'storage/sessions/<id>/session.json', what: 'created_at / last_active', lifetime: 'Session' },
  { path: 'storage/users.db', what: 'Accounts (scrypt hashes) + active logins', lifetime: 'Permanent' },
]
