import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { RefreshCcw, Send } from 'lucide-react'
import { api } from '../services/api'
import { useAuth } from '../hooks/useAuth'
import type { Alert, Case } from '../types'
import FindingLabel from '../components/ui/FindingLabel'
import SeverityBadge from '../components/ui/SeverityBadge'
import Disclaimer from '../components/ui/Disclaimer'

const STATUSES: Alert['status'][] = ['NEW', 'UNDER_REVIEW', 'VERIFIED', 'DISMISSED']

export default function Alerts() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [items, setItems] = useState<Alert[]>([])
  const [cases, setCases] = useState<Case[]>([])
  const [severity, setSeverity] = useState('')
  const [status, setStatus] = useState('')
  const [caseId, setCaseId] = useState('')
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<Alert | null>(null)
  const [note, setNote] = useState('')
  const [running, setRunning] = useState(false)

  const canManage = user?.role === 'ADMINISTRATOR' || user?.role === 'INVESTIGATOR'

  const load = () => {
    setLoading(true)
    const params: any = {}
    if (severity) params.severity = severity
    if (status) params.status = status
    if (caseId) params.case_id = caseId
    api.get('/alerts', { params }).then((res) => setItems(res.data.items)).finally(() => setLoading(false))
  }

  useEffect(() => {
    api.get('/cases', { params: { page_size: 100 } }).then((res) => setCases(res.data.items))
  }, [])

  useEffect(load, [severity, status, caseId])

  const updateAlert = async (alertId: string, payload: any) => {
    await api.patch(`/alerts/${alertId}`, payload)
    load()
    if (selected?.id === alertId) {
      const res = await api.get('/alerts', { params: { severity, status, case_id: caseId } })
      setSelected(res.data.items.find((a: Alert) => a.id === alertId) || null)
    }
  }

  const runDetection = async () => {
    setRunning(true)
    await api.post('/alerts/run-detection').catch(() => {})
    await load()
    setRunning(false)
  }

  return (
    <div>
      <div className="mb-5 flex items-end justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-widest text-muted">NCAS workspace / alert center</div>
          <h1 className="mt-1 text-2xl font-bold">Alerts</h1>
          <p className="text-xs text-muted">Rule-based suspicious-pattern detections awaiting investigator review.</p>
        </div>
        {canManage && (
          <button className="btn" onClick={runDetection} disabled={running}>
            <RefreshCcw size={13} className={running ? 'animate-spin' : ''} /> Re-run detection
          </button>
        )}
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        <select className="input" value={severity} onChange={(e) => setSeverity(e.target.value)}>
          <option value="">All severities</option>
          {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select className="input" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
        </select>
        <select className="input" value={caseId} onChange={(e) => setCaseId(e.target.value)}>
          <option value="">All cases</option>
          {cases.map((c) => <option key={c.id} value={c.id}>{c.id} · {c.title}</option>)}
        </select>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_360px]">
        <div className="panel divide-y divide-line">
          {loading ? (
            <div className="p-8 text-center text-xs text-muted">Loading alerts...</div>
          ) : items.length === 0 ? (
            <div className="p-8 text-center text-xs text-muted">No alerts match these filters.</div>
          ) : (
            items.map((a) => (
              <button
                key={a.id}
                onClick={() => { setSelected(a); setNote('') }}
                className={`flex w-full items-start gap-3 px-4 py-3 text-left hover:bg-white/5 ${selected?.id === a.id ? 'bg-white/5' : ''}`}
              >
                <SeverityBadge severity={a.severity} />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <strong className="text-xs">{a.title}</strong>
                    <FindingLabel label={a.label} />
                  </div>
                  <p className="mt-0.5 truncate text-[11px] text-muted">{a.evidence}</p>
                  <div className="mt-1 flex items-center gap-3 text-[10px] text-muted">
                    <span className="font-mono">{a.id}</span>
                    <span>{a.entity_id}</span>
                    <span className="badge border-line">{a.status.replace('_', ' ')}</span>
                  </div>
                </div>
              </button>
            ))
          )}
        </div>

        <div className="panel p-4">
          <h2 className="mb-3 text-xs font-semibold">Alert detail</h2>
          {!selected ? (
            <p className="text-[11px] text-muted">Select an alert to review it.</p>
          ) : (
            <div className="space-y-3 text-[11px]">
              <div>
                <div className="text-sm font-semibold">{selected.title}</div>
                <FindingLabel label={selected.label} />
              </div>
              <p className="text-slate-300">{selected.evidence}</p>
              <div className="grid grid-cols-2 gap-2">
                <div><span className="text-muted">Detection rule</span><div className="font-mono">{selected.detection_rule}</div></div>
                <div><span className="text-muted">Confidence</span><div>{Math.round(selected.confidence * 100)}%</div></div>
              </div>
              <button className="btn w-full justify-center" onClick={() => navigate(`/entities/${selected.entity_id}`)}>
                View entity {selected.entity_id}
              </button>

              {canManage && (
                <>
                  <div>
                    <label className="mb-1 block text-[10px] uppercase text-muted">Status</label>
                    <div className="flex flex-wrap gap-1">
                      {STATUSES.map((s) => (
                        <button
                          key={s}
                          onClick={() => updateAlert(selected.id, { status: s })}
                          className={`badge ${selected.status === s ? 'border-accent text-accent' : 'border-line text-muted'}`}
                        >
                          {s.replace('_', ' ')}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="mb-1 block text-[10px] uppercase text-muted">Assign to investigator</label>
                    <input
                      className="input w-full"
                      defaultValue={selected.assigned_to}
                      onBlur={(e) => e.target.value !== selected.assigned_to && updateAlert(selected.id, { assigned_to: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-[10px] uppercase text-muted">Add note</label>
                    <div className="flex gap-2">
                      <input className="input flex-1" value={note} onChange={(e) => setNote(e.target.value)} placeholder="Investigator note..." />
                      <button
                        className="btn"
                        onClick={() => { if (note.trim()) { updateAlert(selected.id, { note }); setNote('') } }}
                      >
                        <Send size={12} />
                      </button>
                    </div>
                  </div>
                </>
              )}

              {selected.notes?.length > 0 && (
                <div>
                  <div className="mb-1 text-[10px] uppercase text-muted">Notes</div>
                  <div className="space-y-1">
                    {selected.notes.map((n, i) => (
                      <div key={i} className="rounded-md border border-line px-2 py-1.5">
                        <div className="text-[10px] text-muted">{n.author} · {new Date(n.at).toLocaleString()}</div>
                        <div>{n.text}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <Disclaimer />
    </div>
  )
}
