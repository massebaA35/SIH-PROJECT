import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ShieldCheck, Lock, User as UserIcon, Loader2 } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'

const DEMO_ACCOUNTS = [
  { role: 'Administrator', username: 'admin.demo', password: 'AdminDemo@123' },
  { role: 'Investigator', username: 'investigator.demo', password: 'InvestigatorDemo@123' },
  { role: 'Analyst', username: 'analyst.demo', password: 'AnalystDemo@123' },
]

export default function Login() {
  const { login, error } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    const ok = await login(username, password)
    setSubmitting(false)
    if (ok) navigate('/dashboard')
  }

  const fillDemo = (u: string, p: string) => {
    setUsername(u)
    setPassword(p)
  }

  return (
    <div className="grid min-h-screen place-items-center px-4">
      <div className="w-full max-w-md">
        <div className="mb-6 flex flex-col items-center gap-2 text-center">
          <div className="grid h-12 w-12 place-items-center rounded-xl border border-accent text-accent shadow-[0_0_20px_rgba(34,211,196,0.25)]">
            <ShieldCheck size={22} />
          </div>
          <h1 className="text-lg font-bold tracking-wide">AI-Powered Criminal Network Analysis System</h1>
          <p className="text-xs text-muted">Ministry of Home Affairs · National Crime Records Bureau · Women Safety Division</p>
        </div>

        <form onSubmit={onSubmit} className="panel space-y-4 p-6">
          <div>
            <label className="mb-1 block text-[10px] uppercase tracking-wide text-muted">Username</label>
            <div className="flex items-center gap-2 rounded-md border border-line bg-panel2 px-3 py-2">
              <UserIcon size={14} className="text-muted" />
              <input
                className="w-full bg-transparent text-sm outline-none"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                required
              />
            </div>
          </div>
          <div>
            <label className="mb-1 block text-[10px] uppercase tracking-wide text-muted">Password</label>
            <div className="flex items-center gap-2 rounded-md border border-line bg-panel2 px-3 py-2">
              <Lock size={14} className="text-muted" />
              <input
                type="password"
                className="w-full bg-transparent text-sm outline-none"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </div>
          </div>

          {error ? <p className="rounded-md border border-danger/40 bg-danger/10 px-3 py-2 text-xs text-danger">{error}</p> : null}

          <button type="submit" disabled={submitting} className="btn-primary w-full justify-center py-2.5 disabled:opacity-50">
            {submitting ? <Loader2 size={14} className="animate-spin" /> : null}
            Sign in
          </button>
        </form>

        <div className="panel mt-4 p-4">
          <p className="mb-2 text-[10px] uppercase tracking-wide text-muted">Demo accounts (prototype only)</p>
          <div className="grid gap-2">
            {DEMO_ACCOUNTS.map((acc) => (
              <button
                key={acc.username}
                onClick={() => fillDemo(acc.username, acc.password)}
                className="flex items-center justify-between rounded-md border border-line px-3 py-2 text-left text-[11px] hover:bg-white/5"
              >
                <span className="font-semibold text-slate-200">{acc.role}</span>
                <span className="font-mono text-muted">{acc.username}</span>
              </button>
            ))}
          </div>
          <p className="mt-3 text-[10px] leading-relaxed text-muted">
            These are synthetic demo credentials for local evaluation only. Never reuse them, and never expose real credentials in a
            deployed system.
          </p>
        </div>
      </div>
    </div>
  )
}
