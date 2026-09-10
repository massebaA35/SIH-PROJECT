import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, FolderKanban, Users, Network, Activity, Map as MapIcon,
  Bell, FileText, ShieldCheck, Settings as SettingsIcon, Search, LogOut, ChevronRight,
} from 'lucide-react'
import { useAuth } from '../hooks/useAuth'

const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/cases', label: 'Cases', icon: FolderKanban },
  { to: '/entities', label: 'Entities', icon: Users },
  { to: '/network', label: 'Network Analysis', icon: Network },
  { to: '/timeline', label: 'Timeline', icon: Activity },
  { to: '/map', label: 'Geospatial', icon: MapIcon },
  { to: '/alerts', label: 'Alerts', icon: Bell },
  { to: '/reports', label: 'Reports', icon: FileText },
  { to: '/audit', label: 'Audit Logs', icon: ShieldCheck },
  { to: '/settings', label: 'Settings', icon: SettingsIcon },
]

export default function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')

  const onSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) navigate(`/search?q=${encodeURIComponent(query.trim())}`)
  }

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-60 shrink-0 flex-col border-r border-line bg-panel2 px-3 py-5">
        <div className="mb-6 flex items-center gap-2 px-2">
          <div className="grid h-8 w-8 place-items-center rounded-lg border border-accent text-accent shadow-[0_0_14px_rgba(34,211,196,0.25)]">
            <ShieldCheck size={16} />
          </div>
          <div>
            <div className="text-sm font-bold tracking-wide">NCAS</div>
            <div className="text-[9px] text-muted">NCRB · Women Safety Div.</div>
          </div>
        </div>
        <nav className="flex flex-1 flex-col gap-1">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-md px-3 py-2 text-xs transition-colors ${
                  isActive ? 'bg-white/5 text-accent shadow-[inset_2px_0_0_0_theme(colors.accent)]' : 'text-slate-300 hover:bg-white/5'
                }`
              }
            >
              <Icon size={15} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-line pt-3">
          <div className="flex items-center gap-2 rounded-md px-2 py-1.5 text-[11px] text-muted">
            <span className="h-2 w-2 rounded-full bg-accent shadow-[0_0_0_4px_rgba(34,211,196,0.15)]" />
            Synthetic demo data only
          </div>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center justify-between border-b border-line bg-panel2/60 px-6">
          <div className="flex items-center gap-2 text-xs text-muted">
            <span>Workspace</span>
            <ChevronRight size={13} />
            <span className="text-slate-200">Investigative decision-support</span>
          </div>
          <div className="flex items-center gap-4">
            <form onSubmit={onSearchSubmit} className="flex items-center gap-2 rounded-md border border-line bg-panel2 px-3 py-1.5">
              <Search size={14} className="text-muted" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search cases, persons, phones..."
                className="w-64 bg-transparent text-xs outline-none placeholder:text-muted"
              />
            </form>
            <div className="text-right text-xs">
              <div className="font-semibold text-slate-100">{user?.full_name}</div>
              <div className="text-[10px] text-muted">{user?.role}</div>
            </div>
            <button onClick={logout} className="btn" title="Logout">
              <LogOut size={14} />
            </button>
          </div>
        </header>
        <main className="mx-auto w-full max-w-[1500px] flex-1 px-6 py-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
