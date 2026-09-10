import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, FileText, Fingerprint } from 'lucide-react'
import { api } from '../services/api'
import type { GraphResponse } from '../types'
import CytoscapeGraph from '../components/graph/CytoscapeGraph'
import FindingLabel from '../components/ui/FindingLabel'
import SeverityBadge from '../components/ui/SeverityBadge'
import Disclaimer from '../components/ui/Disclaimer'

export default function CaseDetail() {
  const { caseId } = useParams()
  const navigate = useNavigate()
  const [detail, setDetail] = useState<any>(null)
  const [graph, setGraph] = useState<GraphResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'overview' | 'entities' | 'timeline' | 'evidence' | 'audit'>('overview')

  useEffect(() => {
    if (!caseId) return
    setLoading(true)
    Promise.all([api.get(`/cases/${caseId}`), api.get(`/graph/case/${caseId}`)])
      .then(([caseRes, graphRes]) => {
        setDetail(caseRes.data)
        setGraph(graphRes.data)
      })
      .catch(() => setDetail(null))
      .finally(() => setLoading(false))
  }, [caseId])

  if (loading) return <div className="panel p-10 text-center text-sm text-muted">Loading case...</div>
  if (!detail) return <div className="panel p-10 text-center text-sm text-muted">Case not found.</div>

  const c = detail.case

  return (
    <div>
      <button onClick={() => navigate('/cases')} className="btn mb-4">
        <ArrowLeft size={13} /> Back to cases
      </button>

      <div className="mb-5 flex items-end justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-widest text-muted">{c.id} · {c.category}</div>
          <h1 className="mt-1 text-2xl font-bold">{c.title}</h1>
          <p className="max-w-2xl text-xs text-muted">{detail.description}</p>
        </div>
        <button
          className="btn-primary"
          onClick={() => navigate(`/reports?case_id=${c.id}`)}
        >
          <FileText size={14} /> Generate report
        </button>
      </div>

      <div className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-5">
        {[
          ['Status', c.status], ['Priority', c.priority], ['Risk level', c.risk_level],
          ['Region', c.region], ['Investigator', c.assigned_investigator],
        ].map(([label, value]) => (
          <div key={label} className="panel p-3">
            <div className="text-[10px] uppercase text-muted">{label}</div>
            <div className="mt-1 text-sm font-semibold">{value}</div>
          </div>
        ))}
      </div>

      <div className="mb-4 flex gap-2 border-b border-line">
        {(['overview', 'entities', 'timeline', 'evidence', 'audit'] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`border-b-2 px-3 py-2 text-xs capitalize ${tab === t ? 'border-accent text-accent' : 'border-transparent text-muted hover:text-slate-200'}`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === 'overview' && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <div className="panel p-4 lg:col-span-2">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold">Network graph</h2>
              <button className="btn" onClick={() => navigate(`/network?case_id=${c.id}`)}>Open full analysis</button>
            </div>
            {graph && <CytoscapeGraph nodes={graph.nodes} edges={graph.edges} height={360} colorBy="community" />}
          </div>
          <div className="panel p-4">
            <h2 className="mb-3 text-sm font-semibold">AI analytical observations</h2>
            <p className="mb-3 text-[10px] text-muted">Structural network scoring only. Requires investigator verification.</p>
            <div className="space-y-3">
              {detail.ai_insights.map((insight: any) => (
                <div key={insight.entity_id} className="border-b border-line pb-2 last:border-0">
                  <div className="flex items-center justify-between">
                    <button className="text-xs font-semibold hover:text-accent" onClick={() => navigate(`/entities/${insight.entity_id}`)}>
                      {insight.entity_label}
                    </button>
                    <span className="font-mono text-[11px] text-accent">{insight.network_connectivity_score}/100</span>
                  </div>
                  <FindingLabel label={insight.finding_label} />
                  <p className="mt-1 text-[11px] text-muted">{insight.analytical_interpretation}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {tab === 'entities' && (
        <div className="panel overflow-hidden">
          <div className="grid grid-cols-[1.5fr_.7fr_.6fr_1fr] gap-3 border-b border-line px-4 py-2.5 text-[10px] uppercase text-muted">
            <span>Entity</span><span>Type</span><span>Connections</span><span>Related cases</span>
          </div>
          {detail.related_entities.map((e: any) => (
            <button
              key={e.id}
              onClick={() => navigate(`/entities/${e.id}`)}
              className="grid w-full grid-cols-[1.5fr_.7fr_.6fr_1fr] gap-3 border-b border-line px-4 py-2.5 text-left text-xs last:border-0 hover:bg-white/5"
            >
              <span>{e.label} <small className="font-mono text-muted">{e.id}</small></span>
              <span className="text-muted">{e.type}</span>
              <span>{e.connections}</span>
              <span className="truncate text-muted">{e.related_cases.join(', ')}</span>
            </button>
          ))}
        </div>
      )}

      {tab === 'timeline' && (
        <div className="panel divide-y divide-line">
          {detail.related_events.map((ev: any) => (
            <div key={ev.id} className="px-4 py-3">
              <div className="flex items-center justify-between text-xs">
                <strong>{ev.title}</strong>
                <span className="font-mono text-[10px] text-muted">{new Date(ev.timestamp).toLocaleString()}</span>
              </div>
              <p className="mt-1 text-[11px] text-muted">{ev.description}</p>
            </div>
          ))}
          {detail.related_events.length === 0 && <p className="p-6 text-center text-xs text-muted">No timeline events for this case.</p>}
        </div>
      )}

      {tab === 'evidence' && (
        <div className="panel divide-y divide-line">
          {detail.evidence.map((e: any) => (
            <div key={e.id} className="flex items-start gap-3 px-4 py-3">
              <Fingerprint size={14} className="mt-0.5 text-accent" />
              <div className="min-w-0 flex-1">
                <div className="text-xs font-semibold">{e.type} · {e.id}</div>
                <p className="text-[11px] text-muted">{e.description}</p>
                <div className="mt-1 truncate font-mono text-[10px] text-muted">SHA-256 {e.hash}</div>
              </div>
            </div>
          ))}
          {detail.evidence.length === 0 && <p className="p-6 text-center text-xs text-muted">No evidence records for this case.</p>}
        </div>
      )}

      {tab === 'audit' && (
        <div className="panel divide-y divide-line">
          {detail.audit_history.map((a: any, i: number) => (
            <div key={i} className="flex items-center justify-between px-4 py-2.5 text-xs">
              <span className="font-mono">{a.event_type}</span>
              <span className="text-muted">{a.username}</span>
              <span className="font-mono text-[10px] text-muted">{new Date(a.timestamp).toLocaleString()}</span>
            </div>
          ))}
          {detail.audit_history.length === 0 && <p className="p-6 text-center text-xs text-muted">No audit history references this case yet.</p>}
        </div>
      )}

      <div className="mt-5 panel p-4">
        <h2 className="mb-2 text-sm font-semibold">Alerts</h2>
        <div className="divide-y divide-line">
          {detail.alerts.map((a: any) => (
            <div key={a.id} className="flex items-center gap-3 py-2">
              <SeverityBadge severity={a.severity} />
              <FindingLabel label={a.label} />
              <span className="flex-1 truncate text-xs">{a.title}</span>
            </div>
          ))}
          {detail.alerts.length === 0 && <p className="py-3 text-center text-xs text-muted">No alerts recorded for this case.</p>}
        </div>
      </div>

      <Disclaimer />
    </div>
  )
}
