// Calls the backend auth endpoints (backend/common/auth.py, auth_routes.py).
import { saveAuth, type StoredAuth } from '../../shared/authStorage'
import { endpoints } from '../../shared/endpoints'
import { http } from '../../shared/httpService'

export interface AuthUser {
  email: string
}

interface AuthResponse {
  token: string
  session_id: string
  user: AuthUser
}

function remember(r: AuthResponse): StoredAuth {
  const auth = { email: r.user.email, token: r.token, sessionId: r.session_id }
  saveAuth(auth)
  return auth
}

export async function signIn(email: string, password: string): Promise<StoredAuth> {
  return remember(await http.postJson<AuthResponse>(endpoints.login, { email, password }))
}

export async function signUp(email: string, password: string): Promise<StoredAuth> {
  return remember(await http.postJson<AuthResponse>(endpoints.signup, { email, password }))
}

/** Ends the login on the server, which also deletes the session's document and index. */
export async function signOut(): Promise<void> {
  try {
    await http.post<void>(endpoints.logout)
  } finally {
    saveAuth(null) // log out locally even if the server can't be reached
  }
}

/** Checks a stored login is still valid (e.g. after a page reload). */
export function fetchMe(): Promise<AuthUser> {
  return http.get<AuthUser>(endpoints.me)
}
