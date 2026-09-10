import { useEffect, useState } from 'react'
import { CheckCircle2, Link2, RefreshCcw, ShieldAlert, XCircle } from 'lucide-react'
import { api } from '../services/api'

export default function AuditLogPage() {
  const [logs, setLogs] = useState<any[]>([])
  const [verification, setVerification] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [verifying, setVerifying] = useState(false)
  const [forbidden, setForbidden] = useState(false)

  const load = () => {
    setLoading(true)
    api
      .get('/audit/logs', { params: { limit: 100 } })
      .then((res) => setLogs(res.data.items))
      .catch((err) => { if (err?.response?.status === 403) setForbidden(true) })
      .finally(() => setLoading(false))
  }

  const verify = () => {
    setVerifying(true)
    api
      .get('/audit/verify')
      .then((res) => setVerification(res.data))
      .catch((err) => { if (err?.response?.status === 403) setForbidden(true) })
      .finally(() => setVerifying(false))
  }

  useEffect(() => {
    load()
    verify()
  }, [])

  if (forbidden) {
    return (
      <div className="panel p-10 text-center text-sm text-muted">
        Audit logs are restricted to Administrator and Investigator roles. Sign in with one of those roles to view this page.
      </div>
    )
  }

  return (
    <div>
      <div className="mb-5 flex items-end justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-widest text-muted">NCAS workspace / audit integrity</div>
          <h1 className="mt-1 text-2xl font-bold">Audit logs</h1>
          <p className="text-xs text-muted">Blockchain-inspired tamper-evident audit trail: a SHA-256 hash chain, not a distributed ledger.</p>
        </div>
        <button className="btn" onClick={() => { load(); verify() }}>
          <RefreshCcw size={13} className={verifying ? 'animate-spin' : ''} /> Refresh
        </button>
      </div>

      <div className={`panel mb-4 flex items-center gap-3 p-4 ${verification?.verified === false ? 'border-danger/60' : 'border-accent/40'}`}>
        {verifying ? (
          <RefreshCcw size={18} className="animate-spin text-muted" />
        ) : verification?.verified ? (
          <CheckCircle2 size={20} className="text-accent" />
        ) : (
          <XCircle size={20} className="text-danger" />
        )}
        <div className="flex-1">
          <div className="text-sm font-semibold">
            {verifying ? 'Verifying chain...' : verification?.verified ? 'Audit chain intact' : 'Chain integrity broken'}
          </div>
          <div className="text-[11px] text-muted">{verification?.message}</div>
        </div>
        <div className="text-right text-[11px] text-muted">
          <div>{verification?.records_checked ?? 0} / {verification?.total_records ?? 0} records checked</div>
        </div>
      </div>

      <div className="panel overflow-hidden">
        <div className="grid grid-cols-[80px_1fr_1fr_1fr_120px] gap-3 border-b border-line px-4 py-2.5 text-[10px] uppercase text-muted">
          <span>Seq</span><span>Event</span><span>User</span><span>Timestamp</span><span>Hash</span>
        </div>
        {loading ? (
          <div className="p-8 text-center text-xs text-muted">Loading audit records...</div>
        ) : (
          <div className="max-h-[520px] overflow-y-auto">
            {logs.map((log) => (
              <div key={log.seq} className="grid grid-cols-[80px_1fr_1fr_1fr_120px] items-center gap-3 border-b border-line px-4 py-2.5 text-[11px] last:border-0">
                <span className="font-mono text-muted">#{log.seq}</span>
                <span className="font-mono">{log.event_type}</span>
                <span className="text-muted">{log.username || '—'}</span>
                <span className="font-mono text-[10px] text-muted">{new Date(log.timestamp).toLocaleString()}</span>
                <span className="flex items-center gap-1 truncate font-mono text-[10px] text-muted" title={log.current_hash}>
                  <Link2 size={11} /> {log.current_hash.slice(0, 10)}...
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="mt-4 flex items-start gap-2 text-[11px] text-muted">
        <ShieldAlert size={14} className="mt-0.5 shrink-0 text-accent2" />
        <span>
          Each record's hash commits to the previous record's hash plus its own event data and timestamp. Altering any historical
          record breaks every hash after it, which this verification detects. The architecture can migrate to a permissioned
          blockchain (e.g. Hyperledger Fabric) without changing how the application reads or writes audit events.
        </span>
      </div>
    </div>
  )
}
