import { useEffect, useRef, useState } from 'react'
import cytoscape, { type Core, type ElementDefinition } from 'cytoscape'

type Props = { onSelect: (id: string) => void; graph?: { nodes?: Array<{ id: string; type: string }>; edges?: Array<{ source: string; target: string }> } | null }

const fallbackNodes = ['P001', 'P005', 'P010', 'P014', 'P020', 'P025', 'ORG-001', 'PH-005', 'LOC-003']
const fallbackEdges = [['P001', 'P005'], ['P005', 'P010'], ['P010', 'P014'], ['P014', 'P020'], ['P020', 'P025'], ['P005', 'ORG-001'], ['P014', 'PH-005'], ['P025', 'LOC-003']]

export default function NetworkCanvas({ onSelect, graph }: Props) {
  const container = useRef<HTMLDivElement>(null)
  const instance = useRef<Core | null>(null)
  const [loadedGraph, setLoadedGraph] = useState(graph)
  const [focusType, setFocusType] = useState('ALL')

  useEffect(() => {
    if (graph) {
      setLoadedGraph(graph)
      return
    }
    fetch(`${window.location.protocol}//${window.location.hostname}:8000/api/graph/case/CASE-001`).then(response => response.ok ? response.json() : null).then(setLoadedGraph).catch(() => undefined)
  }, [graph])

  useEffect(() => {
    if (!container.current) return
    const sourceNodes = loadedGraph?.nodes ?? fallbackNodes.map(id => ({ id, type: id.startsWith('ORG') ? 'ORGANIZATION' : id.startsWith('PH') ? 'PHONE' : id.startsWith('LOC') ? 'LOCATION' : 'PERSON' }))
    const sourceEdges = loadedGraph?.edges ?? fallbackEdges.map(([source, target]) => ({ source, target }))
    const focusIds = focusType === 'ALL' ? new Set(sourceNodes.map(node => node.id)) : new Set(sourceNodes.filter(node => node.type === focusType).map(node => node.id))
    if (focusType !== 'ALL') sourceEdges.forEach(edge => { if (focusIds.has(edge.source)) focusIds.add(edge.target); if (focusIds.has(edge.target)) focusIds.add(edge.source) })
    const nodes = sourceNodes.filter(node => focusIds.has(node.id)).slice(0, 20).map(node => ({ data: { id: node.id, type: node.type } }))
    const nodeIds = new Set(nodes.map(node => node.data.id))
    const edges = sourceEdges.filter(edge => nodeIds.has(edge.source) && nodeIds.has(edge.target)).slice(0, 35).map((edge, index) => ({ data: { id: `edge-${index}`, source: edge.source, target: edge.target } }))
    instance.current = cytoscape({ container: container.current, elements: [...nodes, ...edges] as ElementDefinition[], layout: { name: 'cose', animate: false }, style: [
      { selector: 'node', style: { label: 'data(id)', color: '#dce8eb', 'font-size': 10, 'text-valign': 'bottom', 'text-margin-y': 7, 'background-color': '#25c2a0', width: 18, height: 18, 'border-width': 2, 'border-color': '#10242a' } },
      { selector: 'node[type = "ORGANIZATION"]', style: { 'background-color': '#e6a84a' } },
      { selector: 'node[type = "PHONE"]', style: { 'background-color': '#7687ff' } },
      { selector: 'node[type = "LOCATION"]', style: { 'background-color': '#e6789e' } },
      { selector: 'edge', style: { width: 1, 'line-color': '#53676e', 'curve-style': 'bezier' } }
    ] })
    instance.current.on('tap', 'node', event => onSelect(event.target.id()))
    return () => { instance.current?.destroy(); instance.current = null }
  }, [loadedGraph, onSelect, focusType])

  return <div className="network-frame"><div className="network-focus-controls"><span>Focus</span>{[['ALL','All'],['ORGANIZATION','Organizations'],['PERSON','People'],['PHONE','Phones'],['LOCATION','Locations']].map(([value,label])=><button className={focusType===value?'active':''} key={value} onClick={()=>setFocusType(value)}>{label}</button>)}</div><div className="network-canvas cytoscape-canvas" ref={container} aria-label="Interactive case relationship network" /></div>
}
