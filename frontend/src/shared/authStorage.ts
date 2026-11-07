// The current login, as returned by the backend. Kept in localStorage so a refresh or a new
// tab stays logged in. httpService reads it to send the Authorization + X-Session-Id headers.
export interface StoredAuth {
  email: string
  token: string // sent as "Authorization: Bearer <token>"
  sessionId: string // sent as "X-Session-Id"; issued by the server at login
}

const STORAGE_KEY = 'learnai.auth'

let memoryAuth: StoredAuth | null = null // fallback when localStorage is blocked

export function loadAuth(): StoredAuth | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as StoredAuth) : null
  } catch {
    return memoryAuth
  }
}

export function saveAuth(auth: StoredAuth | null) {
  memoryAuth = auth
  try {
    if (auth) localStorage.setItem(STORAGE_KEY, JSON.stringify(auth))
    else localStorage.removeItem(STORAGE_KEY)
  } catch {
    /* storage unavailable (private mode) - login lasts until the tab closes */
  }
}
