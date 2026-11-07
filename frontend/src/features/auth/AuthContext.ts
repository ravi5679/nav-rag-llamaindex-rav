import { createContext } from 'react'
import type { AuthUser } from './authService'

export interface AuthState {
  user: AuthUser | null
  /** Shown on the login page, e.g. "Your session has expired". */
  notice: string
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

export const AuthContext = createContext<AuthState | null>(null)
