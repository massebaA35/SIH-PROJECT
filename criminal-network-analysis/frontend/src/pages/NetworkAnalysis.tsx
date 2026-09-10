import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { GitBranch, Search, Sparkles, Waypoints, X } from 'lucide-react'
import { api } from '../services/api'
import type { Case, GraphResponse } from '../types'
import CytoscapeGraph from '../components/graph/CytoscapeGraph'
import FindingLabel from '../components/ui/FindingLabel'
import Disclaimer from '../components/ui/Disclaimer'

const NODE_TYPES = ['PERSON', 'ORGANIZATION', 'VEHICLE', 'PHONE', 'LOCATION', 'ACCOUNT']
const RELATION_TYPES = [
  'KNOWS', 'CALLED', 'MET', 'WORKED_WITH', 'ASSOCIATED_WITH', 'TRAVELLED_TO',
  'USED', 'TRANSFERRED_TO', 'LINKED_TO_CASE', 'ATTENDED', 'COMMUNICATED_WITH',
]

function shortestPath(edges: GraphResponse['edges'], from: string, to: string): string[] | null {
  const adjacency = new Map<string, string[]>()
  edges.forEach((e) => {
    adjacency.set(e.data.source, [...(adjacency.get(e.data.source) || []), e.data.target])
    adjacency.set(e.data.target, [...(adjacency.get(e.data.target) || []), e.data.source])
  })
  const queue = [[from]]
  const visited = new Set([from])
  while (queue.length) {
    const path = queue.shift()!
    const node = path[path.length - 1]
    if (node === to) return path
    for (const neighbor of adjacency.get(node) || []) {
      if (!visited.has(neighbor)) {
        visited.add(neighbor)
        queue.push([...path, neighbor])
      }
    }
  }
  return null
}

export default function NetworkAnalysis() {
  const [params, setParams] = useSearchParams()
  const [cases, setCases] = useState<Case[]>([])
  const [caseId, setCaseId] = useState(params.get('case_id') || '')
  const [graph, setGraph] = useState<GraphResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [colorBy, setColorBy] = useState<'type' | 'community'>('type')
  const [typeFilter, setTypeFilter] = useState<Set<string>>(new Set(NODE_TYPES))
  const [relationFilter, setRelationFilter] = useState<Set<string>>(new Set(RELATION_TYPES))
  const [query, setQuery] = useState('')
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(params.get('entity_id'))
  const [selectedDetail, setSelectedDetail] = useState<any>(null)
  const [pathFrom, setPathFrom] = useState('')
  const [pathTo, setPathTo] = useState('')
  const [pathNodes, setPathNodes] = useState<Set<string> | null>(null)
  const [showHighConnectivity, setShowHighConnectivity] = useState(false)

  useEffect(() => {
    api.get('/cases', { params: { page_size: 100 } }).then((res) => {
      setCases(res.data.items)
      if (!caseId && !params.get('entity_id') && res.data.items.length) {
        setCaseId(res.data.items[0].id)
      }
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    const entityId = params.get('entity_id')
    setLoading(true)
    const request = entityId
      ? api.get(`/graph/entity/${entityId}`, { params: { depth: 2 } })
      : caseId
        ? api.get(`/graph/case/${caseId}`)
        : null
    if (!request) {
      setLoading(false)
      return
    }
    request
      .then((res) => setGraph(res.data))
      .catch(() => setGraph(null))
      .finally(() => setLoading(false))
  }, [caseId, params])

  useEffect(() => {
    if (!selectedNodeId) {
      setSelectedDetail(null)
      return
    }
    api.get(`/entities/${selectedNodeId}`).then((res) => setSelectedDetail(res.data)).catch(() => setSelectedDetail(null))
  }, [selectedNodeId])

  const filteredNodes = useMemo(() => {
    if (!graph) return []
    let nodes = graph.nodes.filter((n) => typeFilter.has(n.data.type))
    if (query.trim()) {
      const q = query.trim().toLowerCase()
      nodes = nodes.filter((n) => n.data.label.toLowerCase().includes(q) || n.data.id.toLowerCase().includes(q))
    }
    return nodes
  }, [graph, typeFilter, query])

  const visibleIds = useMemo(() => new Set(filteredNodes.map((n) => n.data.id)), [filteredNodes])

  const filteredEdges = useMemo(() => {
    if (!graph) return []
    return graph.edges.filter(
      (e) => relationFilter.has(e.data.relation_type) && visibleIds.has(e.data.source) && visibleIds.has(e.data.target),
    )
  }, [graph, relationFilter, visibleIds])

  const highlighted = useMemo(() => {
    if (pathNodes) return pathNodes
    if (showHighConnectivity && graph) {
      const sorted = [...graph.nodes].sort((a, b) => (b.data.connections || 0) - (a.data.connections || 0))
      const cutoff = sorted[Math.max(0, Math.floor(sorted.length * 0.25) - 1)]?.data.connections ?? 0
      return new Set(graph.nodes.filter((n) => (n.data.connections || 0) >= cutoff && cutoff > 0).map((n) => n.data.id))
    }
    return undefined
  }, [pathNodes, showHighConnectivity, graph])

  const toggleType = (t: string) => {
    setTypeFilter((prev) => {
      const next = new Set(prev)
      next.has(t) ? next.delete(t) : next.add(t)
      return next
    })
  }
  const toggleRelation = (r: string) => {
    setRelationFilter((prev) => {
      const next = new Set(prev)
      next.has(r) ? next.delete(r) : next.add(r)
      return next
    })
  }

  const findPath = () => {
    if (!graph || !pathFrom || !pathTo) return
    const path = shortestPath(graph.edges, pathFrom, pathTo)
    setPathNodes(path ? new Set(path) : new Set())
  }

  const clearEntityMode = () => {
    params.delete('entity_id')
    setParams(params)
  }

  return (
    <div>
      <div className="mb-4 flex items-end justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-widest text-muted">NCAS / graph explorer</div>
          <h1 className="mt-1 text-2xl font-bold">Network analysis</h1>
          <p className="text-xs text-muted">Explore connections, communities, and potential relationships.</p>
        </div>
        <div className="flex items-center gap-2">
          {params.get('entity_id') && (
            <button className="btn" onClick={clearEntityMode}><X size={13} /> Exit entity view</button>
          )}
          <select
            className="input"
            value={caseId}
            onChange={(e) => { setCaseId(e.target.value); clearEntityMode() }}
            disabled={!!params.get('entity_id')}
          >
            {cases.map((c) => (
              <option key={c.id} value={c.id}>{c.id} · {c.title}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_300px]">
        <div className="panel p-3">
          <div className="mb-3 flex flex-wrap items-center gap-3 border-b border-line pb-3">
            <div className="flex items-center gap-2 rounded-md border border-line bg-panel2 px-2.5 py-1.5">
              <Search size={13} className="text-muted" />
              <input
                className="w-40 bg-transparent text-xs outline-none placeholder:text-muted"
                placeholder="Search entity..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
            <div className="flex flex-wrap gap-1">
              {NODE_TYPES.map((t) => (
                <button
                  key={t}
                  onClick={() => toggleType(t)}
                  className={`rounded-full border px-2 py-1 text-[10px] ${typeFilter.has(t) ? 'border-accent/50 bg-accent/10 text-accent' : 'border-line text-muted'}`}
                >
                  {t}
                </button>
              ))}
            </div>
            <button
              onClick={() => setColorBy((c) => (c === 'type' ? 'community' : 'type'))}
              className="btn ml-auto"
            >
              <Sparkles size={13} /> Color by {colorBy === 'type' ? 'community' : 'type'}
            </button>
            <button
              onClick={() => { setShowHighConnectivity((v) => !v); setPathNodes(null) }}
              className={`btn ${showHighConnectivity ? 'border-accent text-accent' : ''}`}
            >
              <GitBranch size={13} /> Highlight highly connected
            </button>
          </div>

          <details className="mb-3 rounded-md border border-line bg-panel2 px-3 py-2">
            <summary className="cursor-pointer text-xs text-muted">Relationship type filters ({relationFilter.size}/{RELATION_TYPES.length})</summary>
            <div className="mt-2 flex flex-wrap gap-1">
              {RELATION_TYPES.map((r) => (
                <button
                  key={r}
                  onClick={() => toggleRelation(r)}
                  className={`rounded-full border px-2 py-1 text-[10px] ${relationFilter.has(r) ? 'border-info/50 bg-info/10 text-info' : 'border-line text-muted'}`}
                >
                  {r}
                </button>
              ))}
            </div>
          </details>

          <div className="mb-3 flex flex-wrap items-center gap-2 rounded-md border border-line bg-panel2 px-3 py-2 text-xs">
            <Waypoints size={13} className="text-accent2" />
            <span className="text-muted">Shortest path:</span>
            <select className="input" value={pathFrom} onChange={(e) => setPathFrom(e.target.value)}>
              <option value="">From...</option>
              {(graph?.nodes || []).map((n) => <option key={n.data.id} value={n.data.id}>{n.data.label}</option>)}
            </select>
            <select className="input" value={pathTo} onChange={(e) => setPathTo(e.target.value)}>
              <option value="">To...</option>
              {(graph?.nodes || []).map((n) => <option key={n.data.id} value={n.data.id}>{n.data.label}</option>)}
            </select>
            <button className="btn" onClick={findPath}>Highlight path</button>
            {pathNodes && (
              <button className="btn" onClick={() => setPathNodes(null)}><X size={12} /> Clear</button>
            )}
            {pathNodes && pathNodes.size === 0 && <span className="text-danger">No path found</span>}
          </div>

          {loading ? (
            <div className="p-16 text-center text-xs text-muted">Loading graph...</div>
          ) : !graph ? (
            <div className="p-16 text-center text-xs text-muted">Select a case to load its network.</div>
          ) : (
            <CytoscapeGraph
              nodes={filteredNodes}
              edges={filteredEdges}
              height={560}
              colorBy={colorBy}
              highlightedNodeIds={highlighted}
              selectedNodeId={selectedNodeId}
              onSelectNode={setSelectedNodeId}
            />
          )}

          <div className="mt-3 flex flex-wrap gap-4 text-[10px] text-muted">
            <span>{filteredNodes.length} entities shown</span>
            <span>{filteredEdges.length} relationships shown</span>
            {graph && <span>{graph.communities.length} communities detected</span>}
          </div>
        </div>

        <div className="space-y-4">
          <div className="panel p-4">
            <h2 className="mb-2 text-xs font-semibold">Communities</h2>
            <div className="space-y-2">
              {(graph?.communities || []).map((c) => (
                <div key={c.id} className="rounded-md border border-line px-2.5 py-2 text-[11px]">
                  <div className="flex items-center justify-between">
                    <strong>{c.label}</strong>
                    <span className="text-muted">{c.size} members</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="panel p-4">
            <h2 className="mb-2 text-xs font-semibold">Potential bridge entities</h2>
            <p className="mb-2 text-[10px] text-muted">Entities whose connections span more than one community.</p>
            <div className="space-y-1">
              {(graph?.bridge_entities || []).map((id) => {
                const node = graph?.nodes.find((n) => n.data.id === id)
                return (
                  <button
                    key={id}
                    onClick={() => setSelectedNodeId(id)}
                    className="flex w-full items-center justify-between rounded-md px-2 py-1.5 text-left text-[11px] hover:bg-white/5"
                  >
                    <span>{node?.data.label || id}</span>
                    <FindingLabel label="Analytical lead" />
                  </button>
                )
              })}
              {(graph?.bridge_entities || []).length === 0 && <p className="text-[11px] text-muted">None identified in this view.</p>}
            </div>
          </div>

          {selectedDetail && (
            <div className="panel p-4">
              <div className="mb-2 flex items-center justify-between">
                <h2 className="text-xs font-semibold">Node details</h2>
                <button onClick={() => setSelectedNodeId(null)} className="text-muted hover:text-slate-200"><X size={13} /></button>
              </div>
              <div className="text-sm font-semibold">{selectedDetail.label}</div>
              <div className="mb-2 text-[10px] text-muted">{selectedDetail.id} · {selectedDetail.type}</div>
              <div className="flex items-center justify-between border-t border-line pt-2">
                <span className="text-[10px] text-muted">Connectivity score</span>
                <span className="font-mono text-accent">{selectedDetail.score}/100</span>
              </div>
              <FindingLabel label={selectedDetail.insight_label} />
              <p className="mt-2 text-[11px] text-muted">{selectedDetail.insight}</p>
              <a href={`/entities/${selectedDetail.id}`} className="btn mt-3 w-full justify-center">Open full profile</a>
            </div>
          )}
        </div>
      </div>

      <Disclaimer text={graph?.disclaimer} />
    </div>
  )
}
