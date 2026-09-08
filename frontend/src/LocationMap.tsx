import { useEffect, useRef } from 'react'
import L from 'leaflet'

const locations: Array<[string, number, number]> = [['Harbor District', 19.076, 72.8777], ['Cedar Junction', 19.0896, 72.8656], ['East Market', 19.0544, 72.8328], ['Riverside Depot', 19.033, 73.0297]]

export default function LocationMap() {
  const container = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!container.current) return
    const map = L.map(container.current, { zoomControl: false }).setView([19.076, 72.8777], 12)
    L.control.zoom({ position: 'bottomright' }).addTo(map)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; OpenStreetMap contributors' }).addTo(map)
    locations.forEach(([label, latitude, longitude]) => L.circleMarker([latitude, longitude], { radius: 8, color: '#25c2a0', fillColor: '#25c2a0', fillOpacity: 0.75 }).addTo(map).bindTooltip(label))
    return () => { map.remove() }
  }, [])
  return <div className="location-map" ref={container} aria-label="Map of case locations" />
}
