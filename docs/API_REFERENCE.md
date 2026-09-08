# NETRA API Reference

## Authentication

All endpoints (except `/api/auth/login`) are public in demo mode. In production, include JWT token in Authorization header:

```
Authorization: Bearer <access_token>
```

### Login
**POST** `/api/auth/login`

Request:
```json
{
  "username": "admin",
  "password": "netra-demo"
}
```

Response:
```json
{
  "access_token": "demo-token",
  "token_type": "bearer",
  "user": {
    "name": "A. Sen",
    "role": "Senior Investigator"
  }
}
```

## Dashboard & Overview

### Get Dashboard
**GET** `/api/dashboard`

Returns KPIs, alerts, and top entities.

Response:
```json
{
  "kpis": [
    {"label": "Active cases", "value": "08", "delta": "+2 this month"},
    ...
  ],
  "alerts": [...],
  "top_entities": [...]
}
```

### List Cases
**GET** `/api/cases`

Returns all investigation cases.

### Get Case Details
**GET** `/api/cases/{case_id}`

Example: `/api/cases/CASE-001`

Returns case information with disclaimer about analytical limitations.

### Get Crime Analysis
**GET** `/api/crime-analysis`

Returns statistical analysis of the crime dataset (record counts, closure rates, demographics, etc.).

## Graph & Network Analysis

### Get Case Graph
**GET** `/api/graph/case/{case_id}?depth={depth}`

Example: `/api/graph/case/CASE-001?depth=2`

Returns:
- `nodes`: Entity list (persons, organizations, phones, locations)
- `edges`: Relationships between entities
- `metrics`: Network analysis metrics (degree, betweenness, closeness, PageRank)
- `communities`: Detected entity clusters

Parameters:
- `depth`: Graph depth (1-3, default: 2)

## Entities

### Search Entities
**GET** `/api/entities?q={query}`

Example: `/api/entities?q=P014`

Filters entities by ID or label.

### Get Entity Profile
**GET** `/api/entities/{entity_id}`

Example: `/api/entities/P014`

Returns:
```json
{
  "id": "P014",
  "label": "Person name",
  "type": "PERSON",
  "status": "person of interest",
  "connections": 8,
  "metrics": {
    "degree": 8,
    "betweenness": 0.12,
    "closeness": 0.45,
    "pagerank": 0.03
  },
  "score": 87,
  "insight": "Person explanation...",
  "evidence": [...]
}
```

### Get Entity Notes
**GET** `/api/entities/{entity_id}/notes`

Returns all notes attached to an entity.

### Add Entity Note
**POST** `/api/entities/{entity_id}/notes`

Request:
```json
{
  "content": "Observed meeting with P025 near Cedar Junction",
  "priority": "high"
}
```

Priority: `low`, `normal`, `high` (default: normal)

Response includes note ID, author, and timestamp.

## Relationships & Evidence

### Get Relationship Notes
**GET** `/api/relationships/{rel_id}/notes`

Returns all notes attached to a relationship.

### Add Relationship Note
**POST** `/api/relationships/{rel_id}/notes`

Same request structure as entity notes.

### Get Pending Review
**GET** `/api/review`

Returns relationships awaiting investigator review.

### Record Review Decision
**POST** `/api/relationships/review`

Request:
```json
{
  "relationship_id": "REL-041",
  "decision": "accepted"
}
```

Decision: `accepted`, `rejected`, `uncertain`

### Upload Document
**POST** `/api/documents/upload`

Supported formats: PDF, TXT, CSV, JSON
Maximum size: 10 MB (configurable)

Response includes:
- Document ID and metadata
- Extracted entities
- SHA-256 hash for integrity verification

### Verify Evidence
**POST** `/api/evidence/{evidence_id}/verify`

Returns evidence hash and chain hash for integrity verification.

## Reports

### Generate Report
**POST** `/api/reports/generate`

Request:
```json
{
  "case_id": "CASE-001"
}
```

Response:
```json
{
  "status": "ready",
  "case_id": "CASE-001",
  "format": "json",
  "sections": [
    "Case Information",
    "Network Overview",
    "Analytical Observations",
    "Evidence Integrity",
    "Limitations"
  ],
  "disclaimer": "..."
}
```

## Timeline

### Get Case Timeline
**GET** `/api/timeline?case_id={case_id}`

Returns chronologically sorted events (relationships and alerts) for a case.

Response:
```json
{
  "case_id": "CASE-001",
  "events": [
    {
      "id": "REL-001",
      "timestamp": "2026-09-04T10:42:00Z",
      "kind": "relationship",
      "title": "P001 CONNECTED_TO P002",
      "description": "Synthetic relationship record",
      "confidence": 0.87,
      "source": "REL-001"
    },
    ...
  ]
}
```

## System Health

### Health Check
**GET** `/api/health`

Returns:
```json
{
  "status": "ok",
  "mode": "synthetic-demo",
  "integrations": {
    "database": false,
    "neo4j": false
  }
}
```

## Error Handling

All endpoints return standard HTTP status codes:
- `200 OK`: Success
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Authentication required
- `404 Not Found`: Resource not found
- `413 Payload Too Large`: File upload exceeds limit
- `500 Internal Server Error`: Server error

Error response:
```json
{
  "detail": "Error message"
}
```

## Rate Limiting

Not implemented in demo mode. Production deployments should add rate limiting middleware.

## Disclaimer

> Analytical scores, graph relationships, and AI-generated insights are not proof of criminal activity or guilt. Investigators must independently verify findings using authorized evidence and applicable procedures.
