import { useEffect, useState } from 'react'
import { Clock, TrendingUp, Users2, GitBranch } from 'lucide-react'
import { api } from '../services/api'
import Disclaimer from '../components/ui/Disclaimer'

interface Snapshot { node_count: number; edge_count: number; community_count: number }
interface TimeMachineResult {
  period: { start: string; end: string }
  before: Snapshot; during: Snapshot; after: Snapshot
  new_entities: string[]; new_relationship_count: number; dormant_entities: string[]
  findings: string[]; disclaimer: string
}

const MS_PER_DAY = 86_400_000

function daysBetween(a: string, b: string): number {
  return Math.round((new Date(b).getTime() - new Date(a).getTime()) / MS_PER_DAY)
}

function addDays(iso: string, days: number): string {
  const d = new Date(iso)
  d.setDate(d.getDate() + days)
  return d.toISOString().slice(0, 10)
}

function SnapshotCard({ title, snap, tone }: { title: string; snap: Snapshot; tone: string }) {
  return (
    <div className="panel p-4">
      <div className={`mb-3 text-[10px] font-semibold uppercase tracking-wide ${tone}`}>{title}</div>
      <div className="grid grid-cols-3 gap-3 text-center">
        <div>
          <div className="font-mono text-xl text-slate-100">{snap.node_count}</div>
          <div className="text-[10px] text-muted">Entities</div>
        </div>
        <div>
          <div className="font-mono text-xl text-slate-100">{snap.edge_count}</div>
          <div className="text-[10px] text-muted">Relationships</div>
        </div>
        <div>
          <div className="font-mono text-xl text-slate-100">{snap.community_count}</div>
          <div className="text-[10px] text-muted">Communities</div>
        </div>
      </div>
    </div>
  )
}

export default function NetworkTimeMachine() {
  const [bounds, setBounds] = useState<{ earliest: string; latest: string } | null>(null)
  const [startOffset, setStartOffset] = useState(0)
  const [endOffset, setEndOffset] = useState(0)
  const [result, setResult] = useState<TimeMachineResult | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.get('/network-time-machine/bounds').then((res) => {
      const { earliest, latest } = res.data
      if (!earliest || !latest) return
      setBounds({ earliest, latest })
      const totalDays = daysBetween(earliest, latest)
      setStartOffset(Math.floor(totalDays * 0.4))
      setEndOffset(Math.floor(totalDays * 0.7))
    })
  }, [])

  const totalDays = bounds ? daysBetween(bounds.earliest, bounds.latest) : 0
  const startDate = bounds ? addDays(bounds.earliest, startOffset) : ''
  const endDate = bounds ? addDays(bounds.earliest, endOffset) : ''

  useEffect(() => {
    if (!bounds || startOffset > endOffset) return
    setLoading(true)
    api.get('/network-time-machine', { params: { start_date: startDate, end_date: endDate } })
      .then((res) => setResult(res.data))
      .finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [startOffset, endOffset, bounds])

  return (
    <div>
      <div className="mb-5">
        <div className="text-[10px] uppercase tracking-widest text-muted">NCAS workspace / network time machine</div>
        <h1 className="mt-1 text-2xl font-bold">Network Time Machine</h1>
        <p className="text-xs text-muted">Slide through recorded activity to see how the network's shape changed before, during, and after a selected period.</p>
      </div>

      {!bounds ? (
        <div className="panel p-10 text-center text-xs text-muted">Loading recorded activity range...</div>
      ) : (
        <>
          <div className="panel mb-4 p-4">
            <div className="mb-3 flex items-center gap-2 text-xs font-semibold text-slate-200">
              <Clock size={14} className="text-accent" /> Selected period: {startDate} → {endDate}
            </div>
            <div className="space-y-3">
              <div>
                <div className="mb-1 flex justify-between text-[10px] text-muted"><span>Period start</span><span className="font-mono">{startDate}</span></div>
                <input
                  type="range" min={0} max={totalDays} value={startOffset}
                  onChange={(e) => setStartOffset(Math.min(Number(e.target.value), endOffset))}
                  className="w-full accent-accent"
                />
              </div>
              <div>
                <div className="mb-1 flex justify-between text-[10px] text-muted"><span>Period end</span><span className="font-mono">{endDate}</span></div>
                <input
                  type="range" min={0} max={totalDays} value={endOffset}
                  onChange={(e) => setEndOffset(Math.max(Number(e.target.value), startOffset))}
                  className="w-full accent-accent"
                />
              </div>
            </div>
            <div className="mt-2 flex justify-between text-[10px] text-muted">
              <span>{bounds.earliest}</span>
              <span>{bounds.latest}</span>
            </div>
          </div>

          {loading || !result ? (
            <div className="panel p-10 text-center text-xs text-muted">Computing network snapshots...</div>
          ) : (
            <>
              <div className="mb-4 grid grid-cols-1 gap-4 md:grid-cols-3">
                <SnapshotCard title="Network before" snap={result.before} tone="text-muted" />
                <SnapshotCard title="Network during selected period" snap={result.during} tone="text-accent" />
                <SnapshotCard title="Network after (cumulative)" snap={result.after} tone="text-accent2" />
              </div>

              <div className="panel mb-4 p-4">
                <div className="mb-3 flex items-center gap-2 text-xs font-semibold text-slate-200">
                  <TrendingUp size={14} className="text-accent" /> Findings
                </div>
                <ul className="space-y-1.5 text-xs text-slate-300">
                  {result.findings.map((f, i) => <li key={i}>• {f}</li>)}
                </ul>
              </div>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="panel p-4">
                  <div className="mb-2 flex items-center gap-2 text-xs font-semibold text-slate-200">
                    <GitBranch size={14} className="text-accent" /> New entities ({result.new_entities.length})
                  </div>
                  {result.new_entities.length === 0 ? (
                    <p className="text-[11px] text-muted">No new entities appeared by the end of this period.</p>
                  ) : (
                    <div className="flex flex-wrap gap-1">
                      {result.new_entities.slice(0, 30).map((id) => <span key={id} className="badge border-line text-slate-300">{id}</span>)}
                    </div>
                  )}
                </div>
                <div className="panel p-4">
                  <div className="mb-2 flex items-center gap-2 text-xs font-semibold text-slate-200">
                    <Users2 size={14} className="text-muted" /> Dormant during this period ({result.dormant_entities.length})
                  </div>
                  {result.dormant_entities.length === 0 ? (
                    <p className="text-[11px] text-muted">Every previously active entity had recorded activity in this period.</p>
                  ) : (
                    <div className="flex flex-wrap gap-1">
                      {result.dormant_entities.slice(0, 30).map((id) => <span key={id} className="badge border-line text-muted">{id}</span>)}
                    </div>
                  )}
                </div>
              </div>

              <Disclaimer text={result.disclaimer} />
            </>
          )}
        </>
      )}
    </div>
  )
}
