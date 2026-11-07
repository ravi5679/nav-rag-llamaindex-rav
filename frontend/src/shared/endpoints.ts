/** The RAG types the backend serves; each has its own endpoints and its own document per session. */
export type RagType = 'naive' | 'hybrid'

export const endpoints = {
  health: '/health',
  signup: '/auth/signup',
  login: '/auth/login',
  logout: '/auth/logout',
  me: '/auth/me',
  stampsVerify: '/stamps/verify',
  stampsReferences: '/stamps/references',
} as const

/** /api/v1/<rag>/query, /ingest, /reindex (backend: common/rag_routes.py) */
export const ragEndpoints = (rag: RagType) => ({
  query: `/${rag}/query`,
  ingest: `/${rag}/ingest`,
  reindex: `/${rag}/reindex`,
})
