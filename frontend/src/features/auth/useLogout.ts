import { startTransition } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from './useAuth'

/** Ends the login (the backend also deletes the session's document) and goes to the home page. */
export function useLogout() {
  const { logout } = useAuth()
  const navigate = useNavigate()

  return () => {
    // Same transition for both updates: if the user were cleared first, ProtectedRoute
    // would still be mounted for one render and redirect to /login instead of home.
    startTransition(() => {
      navigate('/', { replace: true })
      void logout()
    })
  }
}
