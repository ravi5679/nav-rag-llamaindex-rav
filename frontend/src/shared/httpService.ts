import { loadAuth } from './authStorage'
import { API_BASE_URL, API_KEY } from './constants/config'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

// AuthProvider registers this so an expired/invalid login sends the user back to /login
let onUnauthorized: ((message: string) => void) | null = null
export function setUnauthorizedHandler(handler: ((message: string) => void) | null) {
  onUnauthorized = handler
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  if (API_KEY) headers.set('X-API-Key', API_KEY)
  const auth = loadAuth()
  if (auth) {
    headers.set('Authorization', `Bearer ${auth.token}`)
    headers.set('X-Session-Id', auth.sessionId) // the backend checks it belongs to this login
  }

  const res = await fetch(`${API_BASE_URL}${path}`, { ...init, headers })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch {
      /* non-JSON error body */
    }
    // A logged-in request was rejected: the session expired or was ended elsewhere
    if (res.status === 401 && auth) onUnauthorized?.(detail)
    throw new ApiError(res.status, detail)
  }
  if (res.status === 204) return undefined as T // e.g. logout: no body
  return res.json() as Promise<T>
}

export const http = {
  get: <T>(path: string) => request<T>(path),
  postJson: <T>(path: string, body: unknown) =>
    request<T>(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  postForm: <T>(path: string, form: FormData) => request<T>(path, { method: 'POST', body: form }),
  post: <T>(path: string) => request<T>(path, { method: 'POST' }),
}
