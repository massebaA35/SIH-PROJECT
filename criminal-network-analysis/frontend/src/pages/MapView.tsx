import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet.markercluster'
import { api } from '../services/api'
import type { Case } from '../types'

export default function MapView() {
  const mapRef = useRef<HTMLDivElement | null>(null)
  const mapInstance = useRef<L.Map | null>(null)
  const clusterGroup = useRef<L.MarkerClusterGroup | null>(null)

  const [cases, setCases] = useState<Case[]>([])
  const [caseId, setCaseId] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [q, setQ] = useState('')
  const [locations, setLocations] = useState<any[]>([])
  const [selected, setSelected] = useState<any>(null)

  useEffect(() => {
    api.get('/cases', { params: { page_size: 100 } }).then((res) => setCases(res.data.items))
  }, [])

  useEffect(() => {
    if (!mapRef.current || mapInstance.current) return
    const map = L.map(mapRef.current, { zoomControl: true }).setView([22.9, 79.0], 5)
    // Standard OpenStreetMap tiles: free, no API key required. A CSS filter
    // (applied to the tile pane below) gives a dark basemap to match the
    // rest of the UI without depending on a keyed dark-tile provider.
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(map)
    const tilePane = map.getPane('tilePane')
    if (tilePane) {
      tilePane.style.filter = 'invert(1) hue-rotate(180deg) brightness(0.85) contrast(0.9) saturate(0.6)'
    }
    clusterGroup.current = L.markerClusterGroup()
    map.addLayer(clusterGroup.current)
    mapInstance.current = map
  }, [])

  useEffect(() => {
    const params: any = {}
    if (q) params.q = q
    if (caseId) params.case_id = caseId
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    api.get('/locations', { params }).then((res) => setLocations(res.data.items))
  }, [q, caseId, dateFrom, dateTo])

  useEffect(() => {
    if (!clusterGroup.current) return
    clusterGroup.current.clearLayers()
    const maxActivity = Math.max(1, ...locations.map((l) => l.activity_count))
    locations.forEach((loc) => {
      const intensity = loc.activity_count / maxActivity
      const marker = L.circleMarker([loc.latitude, loc.longitude], {
        radius: 7 + intensity * 10,
        color: intensity > 0.66 ? '#f0616b' : intensity > 0.33 ? '#f2a93b' : '#22d3c4',
        fillOpacity: 0.55,
        weight: 1.5,
      })
      marker.bindTooltip(`${loc.name} · ${loc.activity_count} activity records`)
      marker.on('click', () => setSelected(loc))
      clusterGroup.current!.addLayer(marker)
    })
  }, [locations])

  return (
    <div>
      <div className="mb-5">
        <div className="text-[10px] uppercase tracking-widest text-muted">NCAS workspace / geographic intelligence</div>
        <h1 className="mt-1 text-2xl font-bold">Geospatial view</h1>
        <p className="text-xs text-muted">Synthetic location activity across cases, persons, vehicles, and events. City-level only.</p>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        <input className="input w-56" placeholder="Search location or region..." value={q} onChange={(e) => setQ(e.target.value)} />
        <select className="input" value={caseId} onChange={(e) => setCaseId(e.target.value)}>
          <option value="">All cases</option>
          {cases.map((c) => <option key={c.id} value={c.id}>{c.id} · {c.title}</option>)}
        </select>
        <input type="date" className="input" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
        <input type="date" className="input" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_300px]">
        <div className="panel overflow-hidden p-0">
          <div ref={mapRef} style={{ height: 560 }} />
        </div>
        <div className="panel p-4">
          <h2 className="mb-2 text-xs font-semibold">Activity heatmap legend</h2>
          <div className="mb-4 space-y-1 text-[11px] text-muted">
            <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-accent" /> Low activity</div>
            <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-accent2" /> Moderate activity</div>
            <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-danger" /> High activity</div>
          </div>
          <h2 className="mb-2 text-xs font-semibold">Selected location</h2>
          {selected ? (
            <div className="space-y-1 text-[11px]">
              <div className="text-sm font-semibold">{selected.name}</div>
              <div className="text-muted">{selected.region} · {selected.type}</div>
              <div>Activity records: <strong>{selected.activity_count}</strong></div>
              <div className="font-mono text-[10px] text-muted">{selected.latitude.toFixed(3)}, {selected.longitude.toFixed(3)}</div>
            </div>
          ) : (
            <p className="text-[11px] text-muted">Click a marker to view location details.</p>
          )}
          <p className="mt-4 text-[10px] leading-relaxed text-muted">
            {locations.length} locations shown. Coordinates are city-level approximations from the synthetic dataset and never
            resolve to a real private address.
          </p>
        </div>
      </div>
    </div>
  )
}
