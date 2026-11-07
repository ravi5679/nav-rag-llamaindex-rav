import { Navigate, NavLink, Outlet, useParams } from 'react-router-dom'
import { defaultPath, findApp, pagePath } from './menu'

/** Right-hand workspace for one app: title, description, page tabs, then the selected page. */
export function WorkspaceLayout() {
  const { appId } = useParams()
  const app = findApp(appId)
  if (!app) return <Navigate to={defaultPath} replace />

  return (
    <div className="ws">
      <header className="ws-header">
        <span className="ws-icon">
          <app.icon width={28} height={28} />
        </span>
        <div>
          <h1>{app.label}</h1>
          <p className="muted">{app.description}</p>
        </div>
      </header>

      <nav className="ws-tabs" aria-label={`${app.label} sections`}>
        {app.pages.map((page) => (
          <NavLink
            key={page.slug}
            to={pagePath(app, page)}
            className={({ isActive }) => `ws-tab${isActive ? ' active' : ''}`}
          >
            <page.icon width={18} height={18} />
            <span>{page.slug === 'chat' ? 'Chat' : page.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="ws-body">
        <Outlet />
      </div>
    </div>
  )
}
