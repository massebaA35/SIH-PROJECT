import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell,
  LineChart, Line, CartesianGrid, Legend,
} from 'recharts'
import {
  FolderKanban, Users, Building2, Car, MapPin, Phone, Landmark, GitBranch,
  AlertTriangle, Bell, ChevronRight,
} from 'lucide-react'
import { api } from '../services/api'
import FindingLabel from '../components/ui/FindingLabel'
import SeverityBadge from '../components/ui/SeverityBadge'
import StatCard from '../components/ui/StatCard'
import Disclaimer from '../components/ui/Disclaimer'

const ICONS = [FolderKanban, Users, Building2, Car, MapPin, Phone, Landmark, GitBranch, AlertTriangle, Bell]
const TONES: Array<'accent' | 'accent2' | 'info' | 'danger'> = [
  'accent', 'info', 'info', 'accent2', 'info', 'info', 'accent2', 'accent', 'danger', 'danger',
]
const PIE_COLORS = ['#22d3c4', '#f2a93b', '#6f8bff', '#f0616b', '#a78bfa', '#34d399']
const TOOLTIP_STYLE = { background: '#101828', border: '1px solid #22304a', fontSize: 11, color: '#e6edf5' }
const TOOLTIP_LABEL_STYLE = { color: '#8291a8' }
const TOOLTIP_ITEM_STYLE = { color: '#e6edf5' }

interface DashboardData {
  kpis: { label: string; value: number | string; delta: string }[]
  charts: {
    cases_by_category: Record<string, number>
    cases_over_time: Record<string, number>
    network_activity_over_time: Record<string, number>
    entity_distribution: Record<string, number>
    geographic_activity: Record<string, number>
    alert_severity_distribution: Record<string, number>
  }
  alerts: { id: string; severity: string; label: string; title: string; explanation: string; entity: string; time: string }[]
  top_entities: { id: string; label: string; score: number }[]
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [data, setData] = useState<DashboardData | null>(null)
  const [filters, setFilters] = useState({ region: '', category: '', risk_level: '' })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v))
    api
      .get('/dashboard', { params })
      .then((res) => setData(res.data))
      .finally(() => setLoading(false))
  }, [filters])

  const toChartData = (obj: Record<string, number> = {}) => Object.entries(obj).map(([name, value]) => ({ name, value }))

  return (
    <div>
      <div className="mb-5 flex items-end justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-widest text-muted">Case monitoring / live synthetic feed</div>
          <h1 className="mt-1 text-2xl font-bold">Investigation dashboard</h1>
          <p className="text-xs text-muted">Synthetic intelligence signal across active investigations.</p>
        </div>
        <div className="flex gap-2">
          <select className="input" value={filters.risk_level} onChange={(e) => setFilters((f) => ({ ...f, risk_level: e.target.value }))}>
            <option value="">All risk levels</option>
            {['Low', 'Medium', 'High', 'Critical'].map((r) => (
              <option key={r} value={r}>{r} risk</option>
            ))}
          </select>
          <select className="input" value={filters.region} onChange={(e) => setFilters((f) => ({ ...f, region: e.target.value }))}>
            <option value="">All regions</option>
            {['South Zone', 'West Zone', 'North Zone', 'East Zone', 'Coastal Zone'].map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
        </div>
      </div>

      {loading || !data ? (
        <div className="panel p-10 text-center text-sm text-muted">Loading dashboard...</div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
            {data.kpis.map((kpi, i) => (
              <StatCard key={kpi.label} label={kpi.label} value={kpi.value} delta={kpi.delta} icon={ICONS[i] || FolderKanban} tone={TONES[i]} />
            ))}
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
            <div className="panel p-4 lg:col-span-2">
              <h2 className="mb-3 text-sm font-semibold">Cases over time</h2>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={toChartData(data.charts.cases_over_time)}>
                  <CartesianGrid stroke="#22304a" strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#8291a8' }} />
                  <YAxis tick={{ fontSize: 10, fill: '#8291a8' }} allowDecimals={false} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} labelStyle={TOOLTIP_LABEL_STYLE} itemStyle={TOOLTIP_ITEM_STYLE} />
                  <Line type="monotone" dataKey="value" stroke="#22d3c4" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="panel p-4">
              <h2 className="mb-3 text-sm font-semibold">Entity distribution</h2>
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie data={toChartData(data.charts.entity_distribution)} dataKey="value" nameKey="name" innerRadius={40} outerRadius={62} paddingAngle={2}>
                    {toChartData(data.charts.entity_distribution).map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={TOOLTIP_STYLE} labelStyle={TOOLTIP_LABEL_STYLE} itemStyle={TOOLTIP_ITEM_STYLE} />
                  <Legend
                    verticalAlign="bottom"
                    align="center"
                    iconSize={8}
                    wrapperStyle={{ fontSize: 10, color: '#c7d2e0', paddingTop: 8 }}
                    formatter={(value, entry: any) => `${value}: ${entry?.payload?.value ?? ''}`}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
            <div className="panel p-4">
              <h2 className="mb-3 text-sm font-semibold">Cases by category</h2>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={toChartData(data.charts.cases_by_category)} layout="vertical" margin={{ left: 20 }}>
                  <XAxis type="number" tick={{ fontSize: 10, fill: '#8291a8' }} allowDecimals={false} />
                  <YAxis type="category" dataKey="name" width={110} tick={{ fontSize: 9, fill: '#8291a8' }} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} labelStyle={TOOLTIP_LABEL_STYLE} itemStyle={TOOLTIP_ITEM_STYLE} />
                  <Bar dataKey="value" fill="#6f8bff" radius={[0, 3, 3, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="panel p-4">
              <h2 className="mb-3 text-sm font-semibold">Alert severity distribution</h2>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={toChartData(data.charts.alert_severity_distribution)}>
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#8291a8' }} />
                  <YAxis tick={{ fontSize: 10, fill: '#8291a8' }} allowDecimals={false} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} labelStyle={TOOLTIP_LABEL_STYLE} itemStyle={TOOLTIP_ITEM_STYLE} />
                  <Bar dataKey="value" fill="#f0616b" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="panel p-4">
              <h2 className="mb-3 text-sm font-semibold">Geographic activity</h2>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={toChartData(data.charts.geographic_activity)}>
                  <XAxis dataKey="name" tick={{ fontSize: 9, fill: '#8291a8' }} />
                  <YAxis tick={{ fontSize: 10, fill: '#8291a8' }} allowDecimals={false} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} labelStyle={TOOLTIP_LABEL_STYLE} itemStyle={TOOLTIP_ITEM_STYLE} />
                  <Bar dataKey="value" fill="#f2a93b" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
            <div className="panel p-4">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-semibold">Priority alerts</h2>
                <button className="btn" onClick={() => navigate('/alerts')}>
                  View all <ChevronRight size={12} />
                </button>
              </div>
              <div className="divide-y divide-line">
                {data.alerts.map((alert) => (
                  <button
                    key={alert.id}
                    onClick={() => navigate(`/entities/${alert.entity}`)}
                    className="flex w-full items-start gap-3 py-2.5 text-left hover:bg-white/5"
                  >
                    <SeverityBadge severity={alert.severity} />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <strong className="truncate text-xs">{alert.title}</strong>
                        <FindingLabel label={alert.label} />
                      </div>
                      <p className="mt-0.5 truncate text-[11px] text-muted">{alert.explanation}</p>
                    </div>
                  </button>
                ))}
                {data.alerts.length === 0 && <p className="py-4 text-center text-xs text-muted">No alerts recorded.</p>}
              </div>
            </div>

            <div className="panel p-4">
              <h2 className="mb-3 text-sm font-semibold">Most connected entities</h2>
              <div className="divide-y divide-line">
                {data.top_entities.map((item, i) => (
                  <button
                    key={item.id}
                    onClick={() => navigate(`/entities/${item.id}`)}
                    className="flex w-full items-center gap-3 py-2 text-left hover:bg-white/5"
                  >
                    <span className="w-5 font-mono text-[10px] text-muted">{String(i + 1).padStart(2, '0')}</span>
                    <span className="flex-1 truncate text-xs">{item.label}</span>
                    <span className="font-mono text-[11px] text-accent">{item.score}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          <Disclaimer />
        </>
      )}
    </div>
  )
}
