import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, ChevronLeft, ChevronRight } from 'lucide-react'
import { api } from '../services/api'
import type { Case } from '../types'

const STATUS_DOT: Record<string, string> = { Active: 'bg-accent', 'Under review': 'bg-accent2', Closed: 'bg-muted' }

export default function Cases() {
  const navigate = useNavigate()
  const [items, setItems] = useState<Case[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const pageSize = 12
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [priority, setPriority] = useState('')
  const [sortBy, setSortBy] = useState('opened_date')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const handle = setTimeout(() => {
      setLoading(true)
      api
        .get('/cases', { params: { search, status, priority, sort_by: sortBy, sort_dir: 'desc', page, page_size: pageSize } })
        .then((res) => {
          setItems(res.data.items)
          setTotal(res.data.total)
        })
        .finally(() => setLoading(false))
    }, 250)
    return () => clearTimeout(handle)
  }, [search, status, priority, sortBy, page])

  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <div>
      <div className="mb-5 flex items-end justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-widest text-muted">NCAS workspace / case index</div>
          <h1 className="mt-1 text-2xl font-bold">Cases</h1>
          <p className="text-xs text-muted">{total} cases in the synthetic dataset.</p>
        </div>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        <div className="flex items-center gap-2 rounded-md border border-line bg-panel2 px-3 py-2">
          <Search size={13} className="text-muted" />
          <input
            className="w-56 bg-transparent text-xs outline-none placeholder:text-muted"
            placeholder="Search title, id, description..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          />
        </div>
        <select className="input" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1) }}>
          <option value="">All statuses</option>
          <option value="Active">Active</option>
          <option value="Under review">Under review</option>
          <option value="Closed">Closed</option>
        </select>
        <select className="input" value={priority} onChange={(e) => { setPriority(e.target.value); setPage(1) }}>
          <option value="">All priorities</option>
          <option value="low">Low</option>
          <option value="normal">Normal</option>
          <option value="high">High</option>
        </select>
        <select className="input" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
          <option value="opened_date">Sort: date opened</option>
          <option value="title">Sort: title</option>
          <option value="priority">Sort: priority</option>
          <option value="risk_level">Sort: risk level</option>
          <option value="status">Sort: status</option>
        </select>
      </div>

      <div className="panel overflow-hidden">
        <div className="grid grid-cols-[1.8fr_.8fr_.6fr_.6fr_.8fr_16px] gap-4 border-b border-line px-4 py-2.5 text-[10px] uppercase tracking-wide text-muted">
          <span>Case</span>
          <span>Category</span>
          <span>Priority</span>
          <span>Risk</span>
          <span>Investigator</span>
          <span />
        </div>
        {loading ? (
          <div className="p-8 text-center text-xs text-muted">Loading cases...</div>
        ) : items.length === 0 ? (
          <div className="p-8 text-center text-xs text-muted">No cases match these filters.</div>
        ) : (
          items.map((c) => (
            <button
              key={c.id}
              onClick={() => navigate(`/cases/${c.id}`)}
              className="grid w-full grid-cols-[1.8fr_.8fr_.6fr_.6fr_.8fr_16px] items-center gap-4 border-b border-line px-4 py-3 text-left text-xs last:border-0 hover:bg-white/5"
            >
              <span className="flex min-w-0 items-center gap-2">
                <span className={`h-2 w-2 shrink-0 rounded-full ${STATUS_DOT[c.status] || 'bg-muted'}`} />
                <span className="min-w-0">
                  <strong className="block truncate">{c.title}</strong>
                  <small className="font-mono text-[10px] text-muted">{c.id} · {c.opened_date}</small>
                </span>
              </span>
              <span className="truncate text-muted">{c.category}</span>
              <span className="capitalize">{c.priority}</span>
              <span>{c.risk_level}</span>
              <span className="truncate text-muted">{c.assigned_investigator}</span>
              <ChevronRight size={14} className="text-muted" />
            </button>
          ))
        )}
      </div>

      <div className="mt-3 flex items-center justify-between text-xs text-muted">
        <span>Page {page} of {totalPages}</span>
        <div className="flex gap-2">
          <button className="btn" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            <ChevronLeft size={13} /> Prev
          </button>
          <button className="btn" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
            Next <ChevronRight size={13} />
          </button>
        </div>
      </div>
    </div>
  )
}
