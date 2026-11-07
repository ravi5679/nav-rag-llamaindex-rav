import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import ravi3 from '../../assets/Ravi-3.png'
import { useAuth } from './useAuth'
import { hasErrors, MIN_PASSWORD, validateLogin, validateSignup, type AuthErrors } from './validation'
import './auth.css'

type Mode = 'login' | 'signup'

const TEXT = {
  login: { title: 'Welcome back', intro: 'Log in to open your AI learning dashboard.', submit: 'Login', busy: 'Signing in…' },
  signup: { title: 'Create your account', intro: 'Sign up to upload documents and chat with them.', submit: 'Create account', busy: 'Creating account…' },
}

export function LoginPage() {
  const { user, notice, login, signup } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from ?? '/dashboard'

  const [mode, setMode] = useState<Mode>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [errors, setErrors] = useState<AuthErrors>({})
  const [formError, setFormError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/dashboard" replace />

  const switchMode = (next: Mode) => {
    setMode(next)
    setErrors({})
    setFormError('')
    setPassword('')
    setConfirm('')
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError('')
    const v = mode === 'login' ? validateLogin(email, password) : validateSignup(email, password, confirm)
    setErrors(v)
    if (hasErrors(v)) return

    setBusy(true)
    try {
      await (mode === 'login' ? login : signup)(email.trim(), password)
      navigate(from, { replace: true })
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Something went wrong.')
    } finally {
      setBusy(false)
    }
  }

  const t = TEXT[mode]
  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={submit} noValidate>
        <img className="auth-avatar" src={ravi3} alt="Ravi Kumar" />

        <div className="auth-switch" role="tablist" aria-label="Login or sign up">
          <button type="button" role="tab" aria-selected={mode === 'login'} onClick={() => switchMode('login')}>
            Login
          </button>
          <button type="button" role="tab" aria-selected={mode === 'signup'} onClick={() => switchMode('signup')}>
            Sign up
          </button>
        </div>

        <h1>{t.title}</h1>
        <p className="muted">{t.intro}</p>
        {notice && mode === 'login' && <div className="form-notice" role="status">{notice}</div>}

        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          aria-invalid={!!errors.email}
          aria-describedby={errors.email ? 'email-err' : undefined}
          placeholder="you@example.com"
        />
        {errors.email && <span id="email-err" className="field-error">{errors.email}</span>}

        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          aria-invalid={!!errors.password}
          aria-describedby={errors.password ? 'password-err' : mode === 'signup' ? 'password-hint' : undefined}
          placeholder="••••••••"
        />
        {errors.password ? (
          <span id="password-err" className="field-error">{errors.password}</span>
        ) : (
          mode === 'signup' && <span id="password-hint" className="field-hint">At least {MIN_PASSWORD} characters.</span>
        )}

        {mode === 'signup' && (
          <>
            <label htmlFor="confirm">Confirm password</label>
            <input
              id="confirm"
              type="password"
              autoComplete="new-password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              aria-invalid={!!errors.confirm}
              aria-describedby={errors.confirm ? 'confirm-err' : undefined}
              placeholder="••••••••"
            />
            {errors.confirm && <span id="confirm-err" className="field-error">{errors.confirm}</span>}
          </>
        )}

        {formError && <div className="form-error" role="alert">{formError}</div>}

        <button className="btn btn-primary btn-lg" type="submit" disabled={busy}>
          {busy ? t.busy : t.submit}
        </button>

        <p className="auth-alt">
          {mode === 'login' ? (
            <>No account yet? <button type="button" className="link-btn" onClick={() => switchMode('signup')}>Sign up</button></>
          ) : (
            <>Already have an account? <button type="button" className="link-btn" onClick={() => switchMode('login')}>Log in</button></>
          )}
        </p>
        <Link to="/" className="back-link">← Back to home</Link>
      </form>
    </div>
  )
}
