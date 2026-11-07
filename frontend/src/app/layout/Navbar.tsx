import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../features/auth/useAuth'
import { useLogout } from '../../features/auth/useLogout'
import { CloseIcon, MenuIcon } from '../../shared/ui/elements/Icons'
import { Logo } from './Logo'

const links = [
  { to: '/#about', label: 'About' },
  { to: '/#learn', label: "What you'll learn" },
  { to: '/#projects', label: 'Projects' },
  { to: '/#contact', label: 'Contact' },
]

export function Navbar() {
  const { user } = useAuth()
  const logout = useLogout()
  const [open, setOpen] = useState(false)
  const close = () => setOpen(false)

  const handleLogout = () => {
    close()
    logout()
  }

  return (
    <header className="navbar">
      <div className="container navbar-inner">
        <Link to="/" className="brand" onClick={close}>
          <Logo />
        </Link>

        <nav className={`nav-links${open ? ' open' : ''}`} aria-label="Main">
          {links.map((l) => (
            <Link key={l.to} to={l.to} onClick={close}>
              {l.label}
            </Link>
          ))}
          <div className="nav-actions">
            {user ? (
              <>
                <Link to="/dashboard" className="btn btn-ghost btn-sm" onClick={close}>
                  Dashboard
                </Link>
                <button className="btn btn-primary btn-sm" onClick={handleLogout}>
                  Logout
                </button>
              </>
            ) : (
              <Link to="/login" className="btn btn-primary btn-sm" onClick={close}>
                Login
              </Link>
            )}
          </div>
        </nav>

        <button
          className="icon-btn nav-toggle"
          aria-label={open ? 'Close menu' : 'Open menu'}
          aria-expanded={open}
          onClick={() => setOpen((o) => !o)}
        >
          {open ? <CloseIcon /> : <MenuIcon />}
        </button>
      </div>
    </header>
  )
}
