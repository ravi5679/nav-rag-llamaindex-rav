import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { Logo } from '../../app/layout/Logo'
import { ChevronDownIcon, ChevronsLeftIcon } from '../../shared/ui/elements/Icons'
import { findApp, navGroups, pagePath, type AppDef } from './menu'

interface Props {
  /** true while the sidebar is off-screen (mobile drawer closed / desktop collapsed) */
  hidden: boolean
  /** mobile drawer is open */
  open: boolean
  onNavigate: () => void
  onCollapse: () => void
}

/** Expandable section: header button + animated body. Closed bodies are `inert` (no tab stops). */
function Collapsible({
  id, label, icon: Icon, level, expanded, onToggle, children,
}: {
  id: string
  label: string
  icon?: AppDef['icon']
  level: 1 | 2
  expanded: boolean
  onToggle: () => void
  children: React.ReactNode
}) {
  return (
    <div className={`nav-section level-${level}`}>
      <button
        type="button"
        className="nav-head"
        aria-expanded={expanded}
        aria-controls={`nav-${id}`}
        onClick={onToggle}
      >
        {Icon && <Icon width={level === 1 ? 20 : 16} height={level === 1 ? 20 : 16} />}
        <span>{label}</span>
        <ChevronDownIcon className="chev" width={16} height={16} />
      </button>
      <div id={`nav-${id}`} className={`collapse${expanded ? ' is-open' : ''}`}>
        <div className="collapse-inner" inert={!expanded}>
          {children}
        </div>
      </div>
    </div>
  )
}

function PageLinks({ app, onNavigate }: { app: AppDef; onNavigate: () => void }) {
  return (
    <ul className="nav-pages">
      {app.pages.map((page) => (
        <li key={page.slug}>
          <NavLink
            to={pagePath(app, page)}
            onClick={onNavigate}
            className={({ isActive }) => `side-link${isActive ? ' active' : ''}`}
          >
            <page.icon width={16} height={16} />
            <span>{page.label}</span>
          </NavLink>
        </li>
      ))}
    </ul>
  )
}

export function Sidebar({ hidden, open, onNavigate, onCollapse }: Props) {
  const { pathname } = useLocation()
  const activeAppId = pathname.split('/')[2]

  // everything starts expanded, like the design reference
  const [expanded, setExpanded] = useState<Set<string>>(
    () => new Set([...navGroups.map((g) => g.id), ...navGroups.flatMap((g) => g.apps.map((a) => a.id))]),
  )

  // when navigating into an app, make sure its branch is open (the user can still close it afterwards)
  useEffect(() => {
    const app = findApp(activeAppId)
    const group = navGroups.find((g) => g.apps.some((a) => a.id === app?.id))
    if (!app || !group) return
    setExpanded((prev) => {
      if (prev.has(app.id) && prev.has(group.id)) return prev
      return new Set(prev).add(app.id).add(group.id)
    })
  }, [activeAppId])

  const toggle = (id: string) =>
    setExpanded((prev) => {
      const next = new Set(prev)
      if (!next.delete(id)) next.add(id)
      return next
    })

  return (
    <aside className={`sidebar${open ? ' open' : ''}`} aria-label="Dashboard menu" inert={hidden}>
      <div className="sidebar-top">
        <Link to="/" className="sidebar-brand" onClick={onNavigate}>
          <Logo />
        </Link>
        <button
          type="button"
          className="sidebar-collapse"
          aria-label="Collapse sidebar"
          title="Collapse sidebar"
          onClick={onCollapse}
        >
          <ChevronsLeftIcon />
        </button>
      </div>

      <nav className="sidebar-nav" aria-label="Dashboard">
        {navGroups.map((group) => (
          <Collapsible
            key={group.id}
            id={group.id}
            label={group.label}
            icon={group.icon}
            level={1}
            expanded={expanded.has(group.id)}
            onToggle={() => toggle(group.id)}
          >
            {group.flat ? (
              <PageLinks app={group.apps[0]} onNavigate={onNavigate} />
            ) : (
              group.apps.map((app) => (
                <Collapsible
                  key={app.id}
                  id={app.id}
                  label={app.label}
                  icon={app.icon}
                  level={2}
                  expanded={expanded.has(app.id)}
                  onToggle={() => toggle(app.id)}
                >
                  <PageLinks app={app} onNavigate={onNavigate} />
                </Collapsible>
              ))
            )}
          </Collapsible>
        ))}
      </nav>
    </aside>
  )
}
