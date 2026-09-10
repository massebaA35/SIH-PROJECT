import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Fingerprint, Network } from 'lucide-react'
import { api } from '../services/api'
import type { GraphResponse } from '../types'
import CytoscapeGraph from '../components/graph/CytoscapeGraph'
import FindingLabel from '../components/ui/FindingLabel'
import Disclaimer from '../components/ui/Disclaimer'

export default function EntityDetail() {
  const { entityId } = useParams()
  const navigate = useNavigate()
  const [entity, setEntity] = useState<any>(null)
  const [graph, setGraph] = useState<GraphResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!entityId) return
    setLoading(true)
    Promise.all([api.get(`/entities/${entityId}`), api.get(`/graph/entity/${entityId}`, { params: { depth: 1 } })])
      .then(([entityRes, graphRes]) => {
        setEntity(entityRes.data)
        setGraph(graphRes.data)
      })
      .catch(() => setEntity(null))
      .finally(() => setLoading(false))
  }, [entityId])

  if (loading) return <div className="panel p-10 text-center text-sm text-muted">Loading entity...</div>
  if (!entity) return <div className="panel p-10 text-center text-sm text-muted">Entity not found.</div>

  return (
    <div>
      <button onClick={() => navigate(-1)} className="btn mb-4">
        <ArrowLeft size={13} /> Back
      </button>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="panel p-5">
          <div className="mb-4 flex items-center gap-3">
            <div className="grid h-12 w-12 place-items-center rounded-lg bg-accent/15 font-mono text-sm font-bold text-accent">
              {entity.label.slice(0, 2).toUpperCase()}
            </div>
            <div>
              <h1 className="text-lg font-bold">{entity.label}</h1>
              <p className="text-[11px] text-muted">{entity.id} · {entity.type}</p>
            </div>
          </div>

          <div className="flex items-center justify-between border-y border-line py-3">
            <div>
              <div className="text-[10px] text-muted">Investigation priority score</div>
              <div className="mt-1 font-mono text-2xl text-accent">{entity.score}<small className="text-sm text-muted">/100</small></div>
            </div>
            <FindingLabel label={entity.score_label} />
          </div>

          <div className="mt-4">
            <div className="mb-1 flex items-center justify-between">
              <h3 className="text-xs font-semibold">Analytical observation</h3>
              <FindingLabel label={entity.insight_label} />
            </div>
            <p className="rounded-md border-l-2 border-accent2 bg-white/5 p-3 text-[11px] leading-relaxed text-slate-300">{entity.insight}</p>
          </div>

          <div className="mt-4 grid grid-cols-2 gap-px overflow-hidden rounded-md bg-line">
            {Object.entries(entity.metrics || {}).map(([k, v]) => (
              <div key={k} className="bg-panel2 p-2.5">
                <div className="text-[9px] capitalize text-muted">{k.replace(/_/g, ' ')}</div>
                <div className="mt-1 font-mono text-sm">{typeof v === 'number' ? v : String(v)}</div>
              </div>
            ))}
          </div>

          <div className="mt-4">
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-xs font-semibold">Supporting evidence</h3>
              <span className="text-[10px] text-muted">{entity.evidence?.length || 0} records</span>
            </div>
            <div className="space-y-2">
              {(entity.evidence || []).map((e: any) => (
                <div key={e.id} className="flex items-start gap-2 border-t border-line pt-2 text-[11px]">
                  <Fingerprint size={13} className="mt-0.5 shrink-0 text-accent" />
                  <div>
                    <div className="font-semibold">{e.relation} · {e.id}</div>
                    <div className="text-muted">{e.evidence}</div>
                    <div className="mt-0.5 font-mono text-[10px] text-muted">{e.timestamp} · confidence {Math.round(e.confidence * 100)}%</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {entity.related_cases?.length > 0 && (
            <div className="mt-4">
              <h3 className="mb-2 text-xs font-semibold">Related cases</h3>
              <div className="flex flex-wrap gap-2">
                {entity.related_cases.map((cid: string) => (
                  <button key={cid} className="btn" onClick={() => navigate(`/cases/${cid}`)}>{cid}</button>
                ))}
              </div>
            </div>
          )}

          <Disclaimer />
        </div>

        <div className="panel p-4 lg:col-span-2">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-sm font-semibold"><Network size={14} /> Immediate network</h2>
            <button className="btn" onClick={() => navigate(`/network?entity_id=${entity.id}`)}>Open in analysis</button>
          </div>
          {graph && <CytoscapeGraph nodes={graph.nodes} edges={graph.edges} height={520} selectedNodeId={entity.id} />}
        </div>
      </div>
    </div>
  )
}
