# Architecture

## Overview

Two independently runnable services talk over a versioned JSON REST API:

```
frontend/  React + TypeScript + Vite + Tailwind + Cytoscape.js + Recharts + Leaflet
              |
              | HTTPS/JSON, JWT bearer auth
              v
backend/   FastAPI + SQLAlchemy + SQLite (swap to PostgreSQL for production)
              |
              +-- app/models/      SQLAlchemy ORM tables
              +-- app/schemas/     Pydantic request/response validation
              +-- app/routers/     HTTP endpoints (thin -- no business logic)
              +-- app/services/    Cross-cutting read/query logic (entities, search, reports)
              +-- app/graph/       NetworkX graph construction from relational data
              +-- app/analytics/   Centrality, community detection, anomaly rules
              +-- app/ai/          NLP extraction, entity resolution, the AI assistant
              +-- app/security/    JWT, password hashing, RBAC, the audit hash chain
              +-- seed/            Synthetic dataset generator + DB loader
              +-- tests/           pytest suite against an isolated in-memory DB
```

## Why this shape

**Routers stay thin.** Every router function is mostly "validate -> call a
service/analytics function -> shape the response." The actual logic (how to score an
entity, how to detect a community, how to build a report) lives in `services/`,
`analytics/`, `graph/`, and `ai/`, so it's unit-testable without spinning up HTTP.

**The graph is derived, not stored.** There is no persistent graph database. Every
`/api/graph/*` and `/api/analyze/network` call builds a `networkx.MultiGraph` on the
fly from the `relationships` table (`app/graph/graph_builder.py`), runs centrality
and community detection on it, and serializes it to Cytoscape.js's node/edge JSON
shape. This keeps the relational database as the single source of truth and avoids
a second system to keep in sync -- at the dataset size this prototype targets
(hundreds of relationships per case), rebuilding the graph per request is fast enough
not to need caching. `docs/DATABASE.md` covers the migration path to Neo4j/a
dedicated graph store if the dataset grows past that.

**Entities are polymorphic by convention, not by table.** `persons`, `organizations`,
`vehicles`, `phones`, `locations`, and `accounts` are separate tables, but every row's
primary key is a globally unique, type-prefixed string (`PERSON-101`, `VEHICLE-301`,
...). `app/services/entity_service.py` is the one place that knows how to resolve an
id to its table (`entity_type_from_id`) and produce a common "entity summary" shape
across all six tables, so the rest of the codebase (graph builder, search, the AI
assistant) never needs to special-case the entity type.

**Analytics are explainable by construction.** `app/analytics/centrality.py`'s
`explain_entity_score` doesn't just return a number -- it returns the number, the
plain-language reasons behind it, and one of the four required finding labels, and
every caller (case detail, entity detail, network analysis, PDF/JSON reports) reuses
the exact same function so the wording is consistent everywhere in the app. See
`docs/AI_PIPELINE.md` for the full reasoning behind this choice.

**The audit trail is an appended, hash-linked SQL table**, not a separate service --
see `docs/SECURITY.md` for why that's an accurate "blockchain-inspired" description
and not an overclaim.

## Frontend structure

```
frontend/src/
├── pages/            One file per route (Dashboard, Cases, CaseDetail, Entities,
│                      EntityDetail, NetworkAnalysis, Timeline, MapView, Alerts,
│                      SearchPage, Reports, AuditLogPage, Settings, Login)
├── layouts/           AppLayout (sidebar/topbar), ProtectedRoute (auth gate)
├── components/
│   ├── graph/          CytoscapeGraph -- the one graph renderer, reused by
│   │                    NetworkAnalysis, CaseDetail, and EntityDetail
│   └── ui/              FindingLabel, SeverityBadge, StatCard, Disclaimer
├── hooks/useAuth.tsx    Auth context: login/logout, current user, token lifecycle
├── services/api.ts      axios instance with a JWT-attaching interceptor and a
│                        401 -> redirect-to-login interceptor
└── types/index.ts       Shared TypeScript types mirroring the backend's response shapes
```

`CytoscapeGraph` is deliberately the single graph-rendering component in the app: the
Network Analysis page, a case's "network graph" tab, and an entity's "immediate
network" panel all render the exact same node/edge JSON shape the backend returns,
just with different filtering/highlighting layered on top in `NetworkAnalysis.tsx`.

## Request lifecycle (a representative example)

`GET /api/entities/PERSON-101`:

1. `security/rbac.py`'s `get_current_user` dependency decodes the JWT and loads the user.
2. `services/entity_service.get_entity_detail` resolves the id to the `persons` table,
   reads related-case ids from the `relationships` table.
3. Because scoring an entity against its own 1-hop neighborhood would trivially make
   it the most "central" node of that neighborhood (see the regression test
   `test_entity_scores_are_differentiated`), the router instead builds the union of
   every case graph the entity actually belongs to (`nx.compose_all`) and scores the
   entity's position within that real network.
4. `analytics/centrality.compute_centrality` + `explain_entity_score` produce the
   score, label, and reasons.
5. The router assembles the response; no ORM objects leak past the router boundary.

## Migration paths (documented, not built for this prototype)

- **Database:** SQLite -> PostgreSQL is a one-line `DATABASE_URL` change (see
  `docs/DATABASE.md`); every model uses SQLAlchemy's dialect-agnostic column types.
- **Graph store:** if per-request graph construction ever becomes a bottleneck,
  `app/graph/graph_builder.py` is the only module that would need to change to read
  from Neo4j/a graph database instead of `relationships` rows -- callers only see
  `networkx` graphs and wouldn't need to change.
- **Audit chain -> permissioned blockchain:** `app/security/audit_chain.py`'s
  `record_event`/`verify_chain` functions are the only two call sites; swapping the
  SQLite-backed hash chain for a Hyperledger Fabric (or similar) ledger client means
  reimplementing those two functions, not touching any router.
