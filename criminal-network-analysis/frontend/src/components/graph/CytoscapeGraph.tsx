import { useEffect, useRef } from 'react'
import cytoscape, { type Core, type ElementDefinition } from 'cytoscape'
import type { GraphEdge, GraphNode } from '../../types'

const TYPE_COLORS: Record<string, string> = {
  PERSON: '#22d3c4',
  ORGANIZATION: '#f2a93b',
  VEHICLE: '#6f8bff',
  PHONE: '#a78bfa',
  LOCATION: '#f0616b',
  ACCOUNT: '#34d399',
}

const COMMUNITY_PALETTE = ['#22d3c4', '#f2a93b', '#6f8bff', '#f0616b', '#a78bfa', '#34d399', '#fb923c', '#38bdf8']

export interface CytoscapeGraphProps {
  nodes: GraphNode[]
  edges: GraphEdge[]
  height?: number
  colorBy?: 'type' | 'community'
  highlightedNodeIds?: Set<string>
  selectedNodeId?: string | null
  onSelectNode?: (id: string) => void
}

export default function CytoscapeGraph({
  nodes, edges, height = 420, colorBy = 'type', highlightedNodeIds, selectedNodeId, onSelectNode,
}: CytoscapeGraphProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const cyRef = useRef<Core | null>(null)

  useEffect(() => {
    if (!containerRef.current) return

    const elements: ElementDefinition[] = [
      ...nodes.map((n) => ({
        data: n.data as any,
        classes: highlightedNodeIds?.has(n.data.id) ? 'highlighted' : '',
      })),
      ...edges.map((e) => ({ data: e.data as any })),
    ]

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': (ele: any) =>
              colorBy === 'community'
                ? COMMUNITY_PALETTE[(ele.data('community') ?? 0) % COMMUNITY_PALETTE.length]
                : TYPE_COLORS[ele.data('type')] || '#8291a8',
            label: 'data(label)',
            color: '#cbd5e1',
            'font-size': 8,
            'text-valign': 'bottom',
            'text-margin-y': 4,
            width: (ele: any) => 16 + Math.min(24, (ele.data('connections') || 0) * 2),
            height: (ele: any) => 16 + Math.min(24, (ele.data('connections') || 0) * 2),
            'border-width': 1.5,
            'border-color': '#0a0f1a',
          },
        },
        {
          selector: 'node.highlighted',
          style: { 'border-color': '#f2a93b', 'border-width': 3 },
        },
        {
          selector: 'node.selected-node',
          style: { 'border-color': '#ffffff', 'border-width': 3 },
        },
        {
          selector: 'edge',
          style: {
            width: (ele: any) => 1 + Math.min(4, (ele.data('frequency') || 1) * 0.4),
            'line-color': '#3a4a6b',
            'target-arrow-color': '#3a4a6b',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            opacity: 0.75,
          },
        },
        {
          selector: 'edge.dimmed',
          style: { opacity: 0.08 },
        },
        {
          selector: 'node.dimmed',
          style: { opacity: 0.15 },
        },
      ],
      layout: { name: 'cose', animate: false, padding: 30 } as any,
      wheelSensitivity: 0.25,
    })

    cy.on('tap', 'node', (evt) => {
      onSelectNode?.(evt.target.id())
    })

    cyRef.current = cy
    return () => {
      cy.destroy()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, edges, colorBy, highlightedNodeIds])

  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return
    cy.nodes().removeClass('selected-node')
    if (selectedNodeId) {
      cy.getElementById(selectedNodeId).addClass('selected-node')
    }
  }, [selectedNodeId])

  return <div ref={containerRef} style={{ height }} className="rounded-md border border-line bg-panel2" />
}
