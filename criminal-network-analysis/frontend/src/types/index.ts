export type Role = 'ADMINISTRATOR' | 'INVESTIGATOR' | 'ANALYST'
export type FindingLabel = 'Potential connection' | 'Risk indicator' | 'Analytical lead' | 'Requires investigator verification'
export type Severity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
export type AlertStatus = 'NEW' | 'UNDER_REVIEW' | 'VERIFIED' | 'DISMISSED'

export interface User {
  id: string
  username: string
  full_name: string
  email: string
  role: Role
}

export interface Case {
  id: string
  title: string
  category: string
  status: string
  priority: string
  risk_level: string
  region: string
  assigned_investigator: string
  opened_date: string
  updated_at: string
}

export interface EntitySummary {
  id: string
  label: string
  type: string
  connections?: number
}

export interface Alert {
  id: string
  case_id: string
  entity_id: string
  severity: Severity
  detection_rule: string
  label: FindingLabel
  title: string
  evidence: string
  confidence: number
  timestamp: string
  status: AlertStatus
  assigned_to: string
  notes: { author: string; text: string; at: string }[]
}

export interface GraphNode {
  data: {
    id: string
    label: string
    type: string
    connections: number
    community?: number
    degree_centrality?: number
    betweenness_centrality?: number
    closeness_centrality?: number
    pagerank?: number
  }
}

export interface GraphEdge {
  data: {
    id: string
    source: string
    target: string
    relation_type: string
    date: string
    frequency: number
    confidence: number
    evidence: string
  }
}

export interface GraphResponse {
  nodes: GraphNode[]
  edges: GraphEdge[]
  node_count: number
  edge_count: number
  communities: { id: string; label: string; members: string[]; size: number }[]
  bridge_entities: string[]
  disclaimer: string
}
