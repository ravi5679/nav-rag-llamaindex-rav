const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/
export const MIN_PASSWORD = 8 // keep in sync with backend auth.py

export interface AuthErrors {
  email?: string
  password?: string
  confirm?: string
}

export function validateEmail(email: string): string | undefined {
  if (!email.trim()) return 'Email is required.'
  if (!EMAIL_RE.test(email.trim())) return 'Enter a valid email address.'
}

export function validateLogin(email: string, password: string): AuthErrors {
  return { email: validateEmail(email), password: password ? undefined : 'Password is required.' }
}

export function validateSignup(email: string, password: string, confirm: string): AuthErrors {
  let passwordError: string | undefined
  if (!password) passwordError = 'Password is required.'
  else if (password.length < MIN_PASSWORD) passwordError = `Password must be at least ${MIN_PASSWORD} characters.`
  return {
    email: validateEmail(email),
    password: passwordError,
    confirm: confirm === password ? undefined : 'Passwords do not match.',
  }
}

export const hasErrors = (e: AuthErrors) => Boolean(e.email || e.password || e.confirm)
