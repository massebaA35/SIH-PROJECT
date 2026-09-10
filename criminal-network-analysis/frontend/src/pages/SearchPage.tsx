import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Search as SearchIcon } from 'lucide-react'
import { api } from '../services/api'

const TYPE_COLOR: Record<string, string> = {
  CASE: 'bg-purple-400', PERSON: 'bg-accent', ORGANIZATION: 'bg-accent2', VEHICLE: 'bg-info',
  PHONE: 'bg-purple-400', LOCATION: 'bg-danger', ACCOUNT: 'bg-emerald-400',
}

export default function SearchPage() {
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const [query, setQuery] = useState(params.get('q') || '')
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  const runSearch = (q: string) => {
    if (!q.trim()) { setResults([]); return }
    setLoading(true)
    api.post('/search', { query: q }).then((res) => setResults(res.data.results)).finally(() => setLoading(false))
  }

  useEffect(() => {
    const q = params.get('q') || ''
    setQuery(q)
    runSearch(q)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params])

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setParams({ q: query })
  }

  const open = (item: any) => {
    if (item.type === 'CASE') navigate(`/cases/${item.id}`)
    else navigate(`/entities/${item.id}`)
  }

  return (
    <div>
      <div className="mb-5">
        <div className="text-[10px] uppercase tracking-widest text-muted">NCAS workspace / global search</div>
        <h1 className="mt-1 text-2xl font-bold">Search</h1>
        <p className="text-xs text-muted">Search across cases, persons, organizations, vehicles, phones, locations, and accounts.</p>
      </div>

      <form onSubmit={onSubmit} className="mb-4 flex items-center gap-2 rounded-md border border-line bg-panel2 px-3 py-2.5">
        <SearchIcon size={15} className="text-muted" />
        <input
          className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted"
          placeholder="Search by name, id, phone number, plate..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          autoFocus
        />
        <button className="btn-primary">Search</button>
      </form>

      <div className="panel overflow-hidden">
        <div className="grid grid-cols-[1.6fr_.7fr_1fr_.6fr_.8fr] gap-3 border-b border-line px-4 py-2.5 text-[10px] uppercase text-muted">
          <span>Entity</span><span>Type</span><span>Related cases</span><span>Connections</span><span>Last activity</span>
        </div>
        {loading ? (
          <div className="p-8 text-center text-xs text-muted">Searching...</div>
        ) : results.length === 0 ? (
          <div className="p-8 text-center text-xs text-muted">{query ? 'No results found.' : 'Enter a search term to begin.'}</div>
        ) : (
          results.map((r) => (
            <button
              key={`${r.type}-${r.id}`}
              onClick={() => open(r)}
              className="grid w-full grid-cols-[1.6fr_.7fr_1fr_.6fr_.8fr] items-center gap-3 border-b border-line px-4 py-3 text-left text-xs last:border-0 hover:bg-white/5"
            >
              <span className="flex items-center gap-2">
                <span className={`h-2 w-2 rounded-full ${TYPE_COLOR[r.type] || 'bg-muted'}`} />
                <strong>{r.label}</strong> <small className="font-mono text-muted">{r.id}</small>
              </span>
              <span className="text-muted">{r.type}</span>
              <span className="truncate text-muted">{(r.related_cases || []).join(', ') || '—'}</span>
              <span>{r.connection_count ?? '—'}</span>
              <span className="text-muted">{r.last_activity || '—'}</span>
            </button>
          ))
        )}
      </div>
    </div>
  )
}
