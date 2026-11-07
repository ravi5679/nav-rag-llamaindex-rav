import { useEffect, useState } from 'react'
import { Outlet } from 'react-router-dom'
import ravi3 from '../../assets/Ravi-3.png'
import { useAuth } from '../auth/useAuth'
import { useLogout } from '../auth/useLogout'
import { useMediaQuery } from '../../shared/hooks/useMediaQuery'
import { CloseIcon, LogoutIcon, MenuIcon } from '../../shared/ui/elements/Icons'
import { Sidebar } from './Sidebar'
import './dashboard.css'

const COLLAPSED_KEY = 'learnai.sidebar.collapsed'

function loadCollapsed() {
  try {
    return localStorage.getItem(COLLAPSED_KEY) === '1'
  } catch {
    return false
  }
}

export function DashboardLayout() {
  const { user } = useAuth()
  const handleLogout = useLogout()
  const isMobile = useMediaQuery('(max-width: 860px)')
  const [menuOpen, setMenuOpen] = useState(false) // mobile drawer
  const [collapsed, setCollapsed] = useState(loadCollapsed) // desktop

  const setCollapsedPersist = (value: boolean) => {
    setCollapsed(value)
    try {
      localStorage.setItem(COLLAPSED_KEY, value ? '1' : '0')
    } catch {
      /* ignore */
    }
  }

  // Esc closes the mobile drawer
  useEffect(() => {
    if (!menuOpen) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setMenuOpen(false)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [menuOpen])

  const sidebarHidden = isMobile ? !menuOpen : collapsed
  const showToggle = isMobile || collapsed

  const toggleSidebar = () => (isMobile ? setMenuOpen((o) => !o) : setCollapsedPersist(false))
  const collapseSidebar = () => (isMobile ? setMenuOpen(false) : setCollapsedPersist(true))

  return (
    <div className={`dash${!isMobile && collapsed ? ' collapsed' : ''}`}>
      <Sidebar
        hidden={sidebarHidden}
        open={menuOpen}
        onNavigate={() => setMenuOpen(false)}
        onCollapse={collapseSidebar}
      />
      {isMobile && menuOpen && <div className="dash-overlay" onClick={() => setMenuOpen(false)} />}

      <div className="dash-main">
        <header className="dash-topbar">
          {showToggle && (
            <button
              className="icon-btn dash-toggle"
              aria-label={sidebarHidden ? 'Open menu' : 'Close menu'}
              aria-expanded={!sidebarHidden}
              onClick={toggleSidebar}
            >
              {isMobile && menuOpen ? <CloseIcon /> : <MenuIcon />}
            </button>
          )}
          <div className="dash-user">
            <img src={ravi3} alt="" />
            <span className="dash-email">{user?.email}</span>
            <button className="btn btn-ghost btn-sm" onClick={handleLogout}>
              <LogoutIcon width={16} height={16} /> Logout
            </button>
          </div>
        </header>

        <main className="dash-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
