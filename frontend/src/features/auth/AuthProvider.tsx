import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { loadAuth, saveAuth } from '../../shared/authStorage'
import { setUnauthorizedHandler } from '../../shared/httpService'
import { AuthContext } from './AuthContext'
import { fetchMe, signIn, signOut, signUp, type AuthUser } from './authService'

function storedUser(): AuthUser | null {
  const auth = loadAuth()
  return auth ? { email: auth.email } : null
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(storedUser)
  const [notice, setNotice] = useState('')

  // Any request rejected with 401 (expired session, logged out elsewhere) logs out locally
  useEffect(() => {
    setUnauthorizedHandler((message) => {
      saveAuth(null)
      setUser(null)
      setNotice(message)
    })
    return () => setUnauthorizedHandler(null)
  }, [])

  // After a reload, make sure the stored login is still valid on the server
  useEffect(() => {
    // A 401 is handled by the unauthorized handler above; if the backend is down we keep the user
    if (loadAuth()) fetchMe().catch(() => {})
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const auth = await signIn(email, password)
    setNotice('')
    setUser({ email: auth.email })
  }, [])

  const signup = useCallback(async (email: string, password: string) => {
    const auth = await signUp(email, password)
    setNotice('')
    setUser({ email: auth.email })
  }, [])

  const logout = useCallback(async () => {
    setUser(null)
    await signOut().catch(() => {}) // local logout already happened
  }, [])

  const value = useMemo(() => ({ user, notice, login, signup, logout }), [user, notice, login, signup, logout])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
