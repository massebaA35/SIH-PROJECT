import { useEffect, useState } from 'react'
import { Phone, Users, Landmark, Car, FileText, Fingerprint } from 'lucide-react'
import { api } from '../services/api'
import type { Case } from '../types'

const TYPE_ICON: Record<string, any> = {
  CALL: Phone, MEETING: Users, TRANSACTION: Landmark, TRAVEL: Car, CASE_EVENT: FileText, EVIDENCE_EVENT: Fingerprint,
}
const TYPE_COLOR: Record<string, string> = {
  CALL: 'text-info', MEETING: 'text-accent', TRANSACTION: 'text-accent2', TRAVEL: 'text-purple-400',
  CASE_EVENT: 'text-danger', EVIDENCE_EVENT: 'text-emerald-400',
}

export default function Timeline() {
  const [cases, setCases] = useState<Case[]>([])
  const [caseId, setCaseId] = useState('')
  const [eventType, setEventType] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [items, setItems] = useState<any[]>([])
  const [selected, setSelected] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/cases', { params: { page_size: 100 } }).then((res) => setCases(res.data.items))
  }, [])

  useEffect(() => {
    setLoading(true)
    const params: any = {}
    if (caseId) params.case_id = caseId
    if (eventType) params.event_type = eventType
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    api.get('/timeline', { params }).then((res) => setItems(res.data.items)).finally(() => setLoading(false))
  }, [caseId, eventType, dateFrom, dateTo])

  return (
    <div>
      <div className="mb-5">
        <div className="text-[10px] uppercase tracking-widest text-muted">NCAS workspace / investigation timeline</div>
        <h1 className="mt-1 text-2xl font-bold">Timeline</h1>
        <p className="text-xs text-muted">Calls, meetings, transactions, travel, and case events across the synthetic dataset.</p>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        <select className="input" value={caseId} onChange={(e) => setCaseId(e.target.value)}>
          <option value="">All cases</option>
          {cases.map((c) => <option key={c.id} value={c.id}>{c.id} · {c.title}</option>)}
        </select>
        <select className="input" value={eventType} onChange={(e) => setEventType(e.target.value)}>
          <option value="">All event types</option>
          {Object.keys(TYPE_ICON).map((t) => <option key={t} value={t}>{t.replace('_', ' ')}</option>)}
        </select>
        <input type="date" className="input" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
        <input type="date" className="input" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_320px]">
        <div className="panel p-2">
          {loading ? (
            <div className="p-8 text-center text-xs text-muted">Loading timeline...</div>
          ) : items.length === 0 ? (
            <div className="p-8 text-center text-xs text-muted">No events match these filters.</div>
          ) : (
            <div className="max-h-[640px] overflow-y-auto">
              {items.map((ev) => {
                const Icon = TYPE_ICON[ev.type] || FileText
                return (
                  <button
                    key={ev.id}
                    onClick={() => setSelected(ev)}
                    className={`flex w-full items-start gap-3 border-b border-line px-3 py-3 text-left last:border-0 hover:bg-white/5 ${selected?.id === ev.id ? 'bg-white/5' : ''}`}
                  >
                    <Icon size={14} className={`mt-0.5 shrink-0 ${TYPE_COLOR[ev.type] || 'text-muted'}`} />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <strong className="truncate text-xs">{ev.title}</strong>
                        <span className="shrink-0 font-mono text-[10px] text-muted">{new Date(ev.timestamp).toLocaleString()}</span>
                      </div>
                      <p className="mt-0.5 truncate text-[11px] text-muted">{ev.description}</p>
                    </div>
                  </button>
                )
              })}
            </div>
          )}
        </div>

        <div className="panel p-4">
          <h2 className="mb-2 text-xs font-semibold">Event details</h2>
          {!selected ? (
            <p className="text-[11px] text-muted">Select an event to view details.</p>
          ) : (
            <div className="space-y-2 text-[11px]">
              <div><span className="text-muted">Event</span><div className="font-semibold">{selected.title}</div></div>
              <div><span className="text-muted">Case</span><div className="font-mono">{selected.case_id}</div></div>
              <div><span className="text-muted">Type</span><div>{selected.type}</div></div>
              <div><span className="text-muted">Timestamp</span><div className="font-mono">{new Date(selected.timestamp).toLocaleString()}</div></div>
              <div><span className="text-muted">Description</span><div className="text-slate-300">{selected.description}</div></div>
              {selected.related_entities?.length > 0 && (
                <div>
                  <span className="text-muted">Related entities</span>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {selected.related_entities.map((id: string) => (
                      <a key={id} href={`/entities/${id}`} className="badge border-line text-slate-300 hover:border-accent hover:text-accent">{id}</a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
