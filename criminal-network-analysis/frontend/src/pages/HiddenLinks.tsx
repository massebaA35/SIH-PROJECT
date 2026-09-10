import { useEffect, useRef, useState } from 'react'
import { Link2, ArrowDown, Search, Loader2, X } from 'lucide-react'
import { api } from '../services/api'
import Disclaimer from '../components/ui/Disclaimer'
import FindingLabel from '../components/ui/FindingLabel'

const TYPE_COLOR: Record<string, string> = {
  PERSON: 'bg-accent', ORGANIZATION: 'bg-accent2', VEHICLE: 'bg-info',
  PHONE: 'bg-purple-400', LOCATION: 'bg-danger', ACCOUNT: 'bg-emerald-400',
}

interface PathEdge { source: string; target: string; relation_type: string; date: string; confidence: number; evidence: string }
interface PathNode { id: string; type: string; label: string }
interface PathResult { hop_count: number; nodes: PathNode[]; edges: PathEdge[]; confidence: number; spans_multiple_cases: boolean; related_cases: string[]; label: string }
interface EntityOption { id: string; label: string; type: string }

function EntityPicker({ label, placeholder, value, onChange }: {
  label: string; placeholder: string; value: EntityOption | null; onChange: (v: EntityOption | null) => void
}) {
  const [query, setQuery] = useState('')
  const [options, setOptions] = useState<EntityOption[]>([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const boxRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!query.trim() || value) { setOptions([]); return }
    setLoading(true)
    const handle = setTimeout(() => {
      api.get('/entities', { params: { q: query, page: 1, page_size: 8 } })
        .then((res) => setOptions(res.data.items))
        .finally(() => setLoading(false))
    }, 200)
    return () => clearTimeout(handle)
  }, [query, value])

  useEffect(() => {
    const onOutsideClick = (e: MouseEvent) => {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onOutsideClick)
    return () => document.removeEventListener('mousedown', onOutsideClick)
  }, [])

  return (
    <div ref={boxRef} className="relative">
      <label className="mb-1 block text-[10px] uppercase tracking-wide text-muted">{label}</label>
      {value ? (
        <div className="flex w-64 items-center gap-2 rounded-md border border-line bg-panel2 px-3 py-2">
          <span className={`h-2 w-2 shrink-0 rounded-full ${TYPE_COLOR[value.type] || 'bg-muted'}`} />
          <div className="min-w-0 flex-1">
            <div className="truncate text-xs font-semibold">{value.label}</div>
            <div className="font-mono text-[10px] text-muted">{value.id}</div>
          </div>
          <button onClick={() => { onChange(null); setQuery('') }} className="shrink-0 text-muted hover:text-slate-200">
            <X size={13} />
          </button>
        </div>
      ) : (
        <div className="relative w-64">
          <div className="flex items-center gap-2 rounded-md border border-line bg-panel2 px-3 py-2">
            <Search size={13} className="shrink-0 text-muted" />
            <input
              className="w-full bg-transparent text-xs outline-none placeholder:text-muted"
              placeholder={placeholder}
              value={query}
              autoComplete="off"
              onChange={(e) => { setQuery(e.target.value); setOpen(true) }}
              onFocus={() => query.trim() && setOpen(true)}
            />
          </div>
          {open && query.trim() && (
            <div className="absolute left-0 right-0 top-full z-10 mt-1 max-h-64 overflow-y-auto rounded-md border border-line bg-panel2 shadow-lg">
              {loading ? (
                <div className="p-3 text-center text-[11px] text-muted">Searching...</div>
              ) : options.length === 0 ? (
                <div className="p-3 text-center text-[11px] text-muted">No matching entities.</div>
              ) : (
                options.map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => { onChange(opt); setOpen(false); setQuery('') }}
                    className="flex w-full items-center gap-2 border-b border-line px-3 py-2 text-left last:border-0 hover:bg-white/5"
                  >
                    <span className={`h-2 w-2 shrink-0 rounded-full ${TYPE_COLOR[opt.type] || 'bg-muted'}`} />
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-xs">{opt.label}</div>
                      <div className="font-mono text-[10px] text-muted">{opt.id} · {opt.type}</div>
                    </div>
                  </button>
                ))
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function HiddenLinks() {
  const [entityA, setEntityA] = useState<EntityOption | null>(null)
  const [entityB, setEntityB] = useState<EntityOption | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<{ paths: PathResult[]; message?: string; disclaimer?: string } | null>(null)
  const [error, setError] = useState('')

  const findLinks = async () => {
    if (!entityA || !entityB) return
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await api.post('/graph/path', { entity_a: entityA.id, entity_b: entityB.id })
      setResult(res.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Could not search for a connection.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="mb-5">
        <div className="text-[10px] uppercase tracking-widest text-muted">NCAS workspace / hidden link discovery</div>
        <h1 className="mt-1 text-2xl font-bold">Hidden Links</h1>
        <p className="text-xs text-muted">Discover indirect relationships between two entities, including connections that cross case boundaries.</p>
      </div>

      <div className="panel mb-4 p-4">
        <div className="flex flex-wrap items-end gap-3">
          <EntityPicker label="Entity A" placeholder="Search by name or id..." value={entityA} onChange={setEntityA} />
          <Link2 size={16} className="mb-2.5 shrink-0 text-muted" />
          <EntityPicker label="Entity B" placeholder="Search by name or id..." value={entityB} onChange={setEntityB} />
          <button className="btn-primary" disabled={loading || !entityA || !entityB} onClick={findLinks}>
            {loading ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
            Find Hidden Links
          </button>
        </div>
        {error && <p className="mt-3 text-xs text-danger">{error}</p>}
      </div>

      {result && result.paths.length === 0 && (
        <div className="panel p-8 text-center text-xs text-muted">{result.message}</div>
      )}

      {result && result.paths.length > 0 && (
        <div className="space-y-4">
          {result.paths.map((path, i) => (
            <div className="panel p-5" key={i}>
              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <strong className="text-sm">Potential Connection Found</strong>
                  <span className="badge border-line text-muted">{path.hop_count}-hop relationship</span>
                  {path.spans_multiple_cases && <span className="badge border-accent2/40 text-accent2">Spans multiple cases</span>}
                </div>
                <FindingLabel label={path.label as any} />
              </div>

              <div className="flex flex-wrap items-center gap-2">
                {path.nodes.map((node, idx) => (
                  <div key={node.id} className="flex items-center gap-2">
                    <div className="flex items-center gap-2 rounded-md border border-line bg-panel2 px-3 py-2">
                      <span className={`h-2 w-2 rounded-full ${TYPE_COLOR[node.type] || 'bg-muted'}`} />
                      <div>
                        <div className="text-xs font-semibold">{node.label}</div>
                        <div className="font-mono text-[10px] text-muted">{node.id} · {node.type}</div>
                      </div>
                    </div>
                    {idx < path.nodes.length - 1 && (
                      <div className="flex flex-col items-center px-1 text-[10px] text-muted">
                        <ArrowDown size={13} className="rotate-[-90deg]" />
                        <span className="font-mono">{path.edges[idx].relation_type}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
                <div>
                  <div className="mb-1 text-[10px] uppercase text-muted">Evidence along this path</div>
                  <ul className="space-y-1 text-[11px] text-slate-300">
                    {path.edges.map((edge, idx) => (
                      <li key={idx}>
                        <span className="font-mono text-muted">{edge.source} → {edge.target}</span>{' '}
                        ({edge.relation_type.toLowerCase().replace(/_/g, ' ')}{edge.date ? `, ${edge.date}` : ''})
                        {edge.evidence ? ` — ${edge.evidence}` : ''}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <div className="mb-1 text-[10px] uppercase text-muted">Confidence</div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-panel2">
                    <div className="h-full rounded-full bg-accent" style={{ width: `${Math.round(path.confidence * 100)}%` }} />
                  </div>
                  <div className="mt-1 font-mono text-xs text-accent">{Math.round(path.confidence * 100)}%</div>
                  {path.related_cases.length > 0 && (
                    <div className="mt-3">
                      <div className="mb-1 text-[10px] uppercase text-muted">Related cases</div>
                      <div className="flex flex-wrap gap-1">
                        {path.related_cases.map((c) => <span key={c} className="badge border-line text-slate-300">{c}</span>)}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
          {result.disclaimer && <Disclaimer text={result.disclaimer} />}
        </div>
      )}
    </div>
  )
}
