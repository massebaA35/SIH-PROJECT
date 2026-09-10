import { useEffect, useState } from 'react'
import { GitCompare, Loader2 } from 'lucide-react'
import { api } from '../services/api'
import Disclaimer from '../components/ui/Disclaimer'
import FindingLabel from '../components/ui/FindingLabel'
import type { Case } from '../types'

interface Breakdown {
  shared_entities: number; shared_persons: number; shared_organizations: number
  shared_vehicles: number; shared_phones: number; shared_accounts: number
  shared_locations: number; temporal_similarity: string
}
interface CompareResult {
  case_id_a: string; case_id_b: string; similarity_score: number; breakdown: Breakdown
  explanation: string; label: string; disclaimer: string
}
interface RelatedMatch extends CompareResult {}

const BREAKDOWN_ROWS: [keyof Breakdown, string][] = [
  ['shared_persons', 'Shared persons'],
  ['shared_organizations', 'Shared organizations'],
  ['shared_vehicles', 'Shared vehicles'],
  ['shared_phones', 'Shared phones'],
  ['shared_accounts', 'Shared accounts'],
  ['shared_locations', 'Shared locations'],
]

export default function CrossCaseDna() {
  const [cases, setCases] = useState<Case[]>([])
  const [caseA, setCaseA] = useState('')
  const [caseB, setCaseB] = useState('')
  const [result, setResult] = useState<CompareResult | null>(null)
  const [related, setRelated] = useState<RelatedMatch[]>([])
  const [loading, setLoading] = useState(false)
  const [loadingRelated, setLoadingRelated] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/cases', { params: { page_size: 100 } }).then((res) => setCases(res.data.items))
  }, [])

  const compare = async (a = caseA, b = caseB) => {
    if (!a || !b || a === b) return
    setLoading(true)
    setError('')
    try {
      const res = await api.post('/cross-case/compare', { case_id_a: a, case_id_b: b })
      setResult(res.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Could not compare these cases.')
    } finally {
      setLoading(false)
    }
  }

  const findRelated = async () => {
    if (!caseA) return
    setLoadingRelated(true)
    setRelated([])
    try {
      const res = await api.get('/cross-case', { params: { case_id: caseA } })
      setRelated(res.data.matches)
    } finally {
      setLoadingRelated(false)
    }
  }

  const caseLabel = (id: string) => cases.find((c) => c.id === id)?.title || id

  return (
    <div>
      <div className="mb-5">
        <div className="text-[10px] uppercase tracking-widest text-muted">NCAS workspace / cross-case dna</div>
        <h1 className="mt-1 text-2xl font-bold">Cross-Case DNA</h1>
        <p className="text-xs text-muted">Compare two cases for shared entities, shared locations, and temporal overlap.</p>
      </div>

      <div className="panel mb-4 p-4">
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="mb-1 block text-[10px] uppercase tracking-wide text-muted">Case A</label>
            <select className="input w-64" value={caseA} onChange={(e) => setCaseA(e.target.value)}>
              <option value="">Select a case</option>
              {cases.map((c) => <option key={c.id} value={c.id}>{c.id} · {c.title}</option>)}
            </select>
          </div>
          <GitCompare size={16} className="mb-2.5 text-muted" />
          <div>
            <label className="mb-1 block text-[10px] uppercase tracking-wide text-muted">Case B</label>
            <select className="input w-64" value={caseB} onChange={(e) => setCaseB(e.target.value)}>
              <option value="">Select a case</option>
              {cases.map((c) => <option key={c.id} value={c.id}>{c.id} · {c.title}</option>)}
            </select>
          </div>
          <button className="btn-primary" disabled={loading || !caseA || !caseB || caseA === caseB} onClick={() => compare()}>
            {loading ? <Loader2 size={14} className="animate-spin" /> : <GitCompare size={14} />}
            Compare
          </button>
          <button className="btn" disabled={loadingRelated || !caseA} onClick={findRelated}>
            {loadingRelated ? <Loader2 size={14} className="animate-spin" /> : null}
            Find related cases
          </button>
        </div>
        {error && <p className="mt-3 text-xs text-danger">{error}</p>}
      </div>

      {result && (
        <div className="panel mb-4 p-5">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-3 text-sm">
              <strong>{result.case_id_a}</strong>
              <span className="rounded-full border border-accent/40 bg-accent/10 px-3 py-1 font-mono text-accent">{result.similarity_score}% similarity</span>
              <strong>{result.case_id_b}</strong>
            </div>
            <FindingLabel label={result.label as any} />
          </div>

          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            {BREAKDOWN_ROWS.filter(([key]) => result.breakdown[key] as number > 0).map(([key, label]) => (
              <div key={key} className="rounded-md border border-line bg-panel2 p-3">
                <div className="text-[10px] uppercase text-muted">{label}</div>
                <div className="mt-1 font-mono text-lg text-accent">{result.breakdown[key]}</div>
              </div>
            ))}
            <div className="rounded-md border border-line bg-panel2 p-3">
              <div className="text-[10px] uppercase text-muted">Temporal similarity</div>
              <div className="mt-1 text-lg font-semibold">{result.breakdown.temporal_similarity}</div>
            </div>
          </div>

          <div className="mt-4 border-t border-line pt-3">
            <div className="mb-1 text-[10px] uppercase text-muted">Why are these cases similar?</div>
            <p className="text-xs text-slate-300">{result.explanation}</p>
          </div>
          <Disclaimer text={result.disclaimer} />
        </div>
      )}

      {related.length > 0 && (
        <div className="panel overflow-hidden">
          <div className="border-b border-line bg-panel2 px-4 py-3">
            <h3 className="text-xs font-semibold">Cases with a similar network signature to {caseLabel(caseA)}</h3>
          </div>
          <div className="divide-y divide-line">
            {related.map((m) => (
              <button
                key={m.case_id_b}
                onClick={() => { setCaseB(m.case_id_b); compare(caseA, m.case_id_b) }}
                className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left text-xs hover:bg-white/5"
              >
                <span><strong>{m.case_id_b}</strong> <span className="text-muted">{caseLabel(m.case_id_b)}</span></span>
                <span className="font-mono text-accent">{m.similarity_score}%</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
