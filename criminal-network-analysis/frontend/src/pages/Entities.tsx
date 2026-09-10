import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, ChevronLeft, ChevronRight, ChevronRight as Arrow } from 'lucide-react'
import { api } from '../services/api'

const TYPE_COLOR: Record<string, string> = {
  PERSON: 'bg-accent', ORGANIZATION: 'bg-accent2', VEHICLE: 'bg-info',
  PHONE: 'bg-purple-400', LOCATION: 'bg-danger', ACCOUNT: 'bg-emerald-400',
}

export default function Entities() {
  const navigate = useNavigate()
  const [items, setItems] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [type, setType] = useState('')
  const [q, setQ] = useState('')
  const [page, setPage] = useState(1)
  const pageSize = 15
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const handle = setTimeout(() => {
      setLoading(true)
      api
        .get('/entities', { params: { type: type || undefined, q, page, page_size: pageSize } })
        .then((res) => {
          setItems(res.data.items)
          setTotal(res.data.total)
        })
        .finally(() => setLoading(false))
    }, 250)
    return () => clearTimeout(handle)
  }, [type, q, page])

  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <div>
      <div className="mb-5 flex items-end justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-widest text-muted">NCAS workspace / entity index</div>
          <h1 className="mt-1 text-2xl font-bold">Entities</h1>
          <p className="text-xs text-muted">{total} entities across persons, organizations, vehicles, phones, locations, and accounts.</p>
        </div>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        <div className="flex items-center gap-2 rounded-md border border-line bg-panel2 px-3 py-2">
          <Search size={13} className="text-muted" />
          <input
            className="w-56 bg-transparent text-xs outline-none placeholder:text-muted"
            placeholder="Search by name or id..."
            value={q}
            onChange={(e) => { setQ(e.target.value); setPage(1) }}
          />
        </div>
        <select className="input" value={type} onChange={(e) => { setType(e.target.value); setPage(1) }}>
          <option value="">All entity types</option>
          {['PERSON', 'ORGANIZATION', 'VEHICLE', 'PHONE', 'LOCATION', 'ACCOUNT'].map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      <div className="panel overflow-hidden">
        <div className="grid grid-cols-[1.6fr_.8fr_.6fr_16px] gap-4 border-b border-line px-4 py-2.5 text-[10px] uppercase text-muted">
          <span>Entity</span><span>Type</span><span>Connections</span><span />
        </div>
        {loading ? (
          <div className="p-8 text-center text-xs text-muted">Loading entities...</div>
        ) : items.length === 0 ? (
          <div className="p-8 text-center text-xs text-muted">No entities match this search.</div>
        ) : (
          items.map((e) => (
            <button
              key={e.id}
              onClick={() => navigate(`/entities/${e.id}`)}
              className="grid w-full grid-cols-[1.6fr_.8fr_.6fr_16px] items-center gap-4 border-b border-line px-4 py-3 text-left text-xs last:border-0 hover:bg-white/5"
            >
              <span className="flex items-center gap-2">
                <span className={`h-2 w-2 rounded-full ${TYPE_COLOR[e.type] || 'bg-muted'}`} />
                <strong>{e.label}</strong> <small className="font-mono text-muted">{e.id}</small>
              </span>
              <span className="text-muted">{e.type}</span>
              <span>{e.connections}</span>
              <Arrow size={14} className="text-muted" />
            </button>
          ))
        )}
      </div>

      <div className="mt-3 flex items-center justify-between text-xs text-muted">
        <span>Page {page} of {totalPages}</span>
        <div className="flex gap-2">
          <button className="btn" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}><ChevronLeft size={13} /> Prev</button>
          <button className="btn" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>Next <ChevronRight size={13} /></button>
        </div>
      </div>
    </div>
  )
}
