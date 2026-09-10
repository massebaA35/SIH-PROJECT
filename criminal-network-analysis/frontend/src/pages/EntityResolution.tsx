import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CheckCircle, RefreshCcw, ShieldAlert, XCircle } from 'lucide-react'
import { api } from '../services/api'
import Disclaimer from '../components/ui/Disclaimer'

interface Indicators { name_similarity: number; phone_overlap: number; location_overlap: number; organization_overlap: number }
interface Candidate {
  entity_a: { id: string; name: string }; entity_b: { id: string; name: string }
  confidence: number; indicators: Indicators; possible_matching_attributes: string[]
  label: string; recommendation: string
}

const INDICATOR_LABELS: [keyof Indicators, string][] = [
  ['name_similarity', 'Name similarity'],
  ['phone_overlap', 'Phone overlap'],
  ['location_overlap', 'Location overlap'],
  ['organization_overlap', 'Organization overlap'],
]

function IndicatorBar({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-[10px] text-muted">
        <span>{label}</span>
        <span className="font-mono">{Math.round(value * 100)}%</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-panel2">
        <div className="h-full rounded-full bg-accent" style={{ width: `${Math.round(value * 100)}%` }} />
      </div>
    </div>
  )
}

export default function EntityResolution() {
  const navigate = useNavigate()
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [loading, setLoading] = useState(true)
  const [decisions, setDecisions] = useState<Record<string, 'CONFIRMED' | 'DISMISSED'>>({})
  const [submitting, setSubmitting] = useState<string | null>(null)

  const pairKey = (c: Candidate) => `${c.entity_a.id}::${c.entity_b.id}`

  const load = () => {
    setLoading(true)
    api.get('/entities/resolution/duplicates').then((res) => setCandidates(res.data.candidates)).finally(() => setLoading(false))
  }

  useEffect(load, [])

  const decide = async (c: Candidate, decision: 'CONFIRMED' | 'DISMISSED') => {
    const key = pairKey(c)
    setSubmitting(key)
    try {
      await api.post('/entities/resolution/decision', { entity_a: c.entity_a.id, entity_b: c.entity_b.id, decision })
      setDecisions((prev) => ({ ...prev, [key]: decision }))
    } finally {
      setSubmitting(null)
    }
  }

  return (
    <div>
      <div className="mb-5 flex items-end justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-widest text-muted">NCAS workspace / entity resolution assistant</div>
          <h1 className="mt-1 text-2xl font-bold">Entity Resolution</h1>
          <p className="text-xs text-muted">Possible duplicate person records, surfaced for investigator confirmation. Nothing here is ever merged automatically.</p>
        </div>
        <button className="btn text-xs" onClick={load}>
          <RefreshCcw size={13} className={loading ? 'animate-spin' : ''} /> Refresh
        </button>
      </div>

      <div className="panel mb-4 p-4">
        <div className="flex items-start gap-3">
          <ShieldAlert size={18} className="mt-0.5 shrink-0 text-accent2" />
          <p className="text-xs text-muted">
            Every candidate below is an <strong className="text-slate-200">analytical lead</strong>, not a confirmed identity match.
            Confirming a match records your decision to the tamper-evident audit trail; it does not merge or alter any underlying record.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="panel p-10 text-center text-xs text-muted">Scanning for potential duplicate records...</div>
      ) : candidates.length === 0 ? (
        <div className="panel p-10 text-center text-xs text-muted">No potential duplicate candidates detected above the confidence threshold.</div>
      ) : (
        <div className="space-y-3">
          {candidates.map((c) => {
            const key = pairKey(c)
            const decision = decisions[key]
            return (
              <div key={key} className="panel p-4">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="rounded-md border border-accent/40 bg-accent/10 px-3 py-1.5 text-center font-mono text-sm text-accent">
                      {Math.round(c.confidence * 100)}%
                    </div>
                    <div>
                      <div className="flex items-center gap-2 text-sm">
                        <button className="font-semibold text-slate-100 hover:text-accent" onClick={() => navigate(`/entities/${c.entity_a.id}`)}>{c.entity_a.name}</button>
                        <span className="text-muted">↔</span>
                        <button className="font-semibold text-slate-100 hover:text-accent" onClick={() => navigate(`/entities/${c.entity_b.id}`)}>{c.entity_b.name}</button>
                      </div>
                      <div className="mt-1 font-mono text-[10px] text-muted">{c.entity_a.id} · {c.entity_b.id}</div>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {c.possible_matching_attributes.map((attr, i) => (
                          <span key={i} className="rounded bg-white/5 px-1.5 py-0.5 text-[10px] text-slate-300">{attr}</span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {decision ? (
                      <span className={`rounded px-2.5 py-1.5 text-[11px] font-semibold ${decision === 'CONFIRMED' ? 'bg-accent/20 text-accent' : 'bg-white/5 text-muted'}`}>
                        {decision === 'CONFIRMED' ? 'Investigator confirmed' : 'Kept separate'}
                      </span>
                    ) : (
                      <>
                        <button
                          disabled={submitting === key}
                          onClick={() => decide(c, 'CONFIRMED')}
                          className="flex items-center gap-1 rounded bg-accent/15 px-3 py-1.5 text-[11px] font-medium text-accent hover:bg-accent/25 disabled:opacity-50"
                        >
                          <CheckCircle size={12} /> Confirm Match
                        </button>
                        <button
                          disabled={submitting === key}
                          onClick={() => decide(c, 'DISMISSED')}
                          className="flex items-center gap-1 rounded border border-line px-3 py-1.5 text-[11px] text-muted hover:bg-white/5 hover:text-slate-200 disabled:opacity-50"
                        >
                          <XCircle size={12} /> Keep Separate
                        </button>
                      </>
                    )}
                  </div>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-4 border-t border-line pt-3 sm:grid-cols-4">
                  {INDICATOR_LABELS.map(([field, label]) => (
                    <IndicatorBar key={field} label={label} value={c.indicators[field]} />
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}

      <Disclaimer text="Entity resolution findings represent probabilistic similarity leads only and do not automatically alter database records without investigator confirmation." />
    </div>
  )
}
