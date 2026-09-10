import { ShieldCheck } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { API_BASE_URL } from '../services/api'

export default function Settings() {
  const { user } = useAuth()

  return (
    <div>
      <div className="mb-5">
        <div className="text-[10px] uppercase tracking-widest text-muted">NCAS workspace / settings</div>
        <h1 className="mt-1 text-2xl font-bold">Settings</h1>
        <p className="text-xs text-muted">Session and platform information.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="panel p-5">
          <h2 className="mb-3 text-sm font-semibold">Account</h2>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between border-b border-line pb-2"><span className="text-muted">Full name</span><span>{user?.full_name}</span></div>
            <div className="flex justify-between border-b border-line pb-2"><span className="text-muted">Username</span><span className="font-mono">{user?.username}</span></div>
            <div className="flex justify-between border-b border-line pb-2"><span className="text-muted">Role</span><span>{user?.role}</span></div>
            <div className="flex justify-between"><span className="text-muted">Email</span><span>{user?.email}</span></div>
          </div>
        </div>

        <div className="panel p-5">
          <h2 className="mb-3 text-sm font-semibold">Platform</h2>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between border-b border-line pb-2"><span className="text-muted">API base URL</span><span className="font-mono">{API_BASE_URL}</span></div>
            <div className="flex justify-between border-b border-line pb-2"><span className="text-muted">Dataset</span><span>Synthetic demo data only</span></div>
            <div className="flex justify-between"><span className="text-muted">API documentation</span><a className="text-accent underline" href={API_BASE_URL.replace(/\/api$/, '/docs')} target="_blank" rel="noreferrer">Open Swagger docs</a></div>
          </div>
        </div>

        <div className="panel p-5 lg:col-span-2">
          <div className="mb-2 flex items-center gap-2 text-sm font-semibold"><ShieldCheck size={15} className="text-accent" /> Role-based access</div>
          <table className="w-full text-left text-[11px]">
            <thead className="text-muted">
              <tr>
                <th className="pb-2">Role</th>
                <th className="pb-2">Read investigative data</th>
                <th className="pb-2">Review/update alerts</th>
                <th className="pb-2">View audit logs</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              <tr><td className="py-2">Administrator</td><td>Yes</td><td>Yes</td><td>Yes</td></tr>
              <tr><td className="py-2">Investigator</td><td>Yes</td><td>Yes</td><td>Yes</td></tr>
              <tr><td className="py-2">Analyst</td><td>Yes</td><td>No</td><td>No</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
