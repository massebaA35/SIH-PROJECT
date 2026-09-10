# API reference

Base URL: `http://localhost:8010/api` (adjust port to however you started uvicorn).
Full interactive docs with live "Try it out" are auto-generated at `/docs` (Swagger)
and `/redoc` while the backend is running -- this file is a hand-written companion,
not a duplicate of the generated schema.

All endpoints except `/`, `/api/health`, and `/api/auth/login` require
`Authorization: Bearer <token>`. Endpoints that write data (`PATCH /api/alerts/*`,
`POST /api/alerts/run-detection`) additionally require the `ADMINISTRATOR` or
`INVESTIGATOR` role; `GET /api/audit/*` requires the same two roles.

## Auth

**`POST /api/auth/login`** -- no auth required.
```json
// request
{"username": "investigator.demo", "password": "InvestigatorDemo@123"}
// response 200
{"access_token": "...", "token_type": "bearer", "user": {"id": "USER-002", "username": "investigator.demo", "full_name": "A. Sen", "email": "...", "role": "INVESTIGATOR"}}
```
Returns 401 on a bad username/password (and records a `LOGIN_FAILED` audit event).

**`GET /api/auth/me`** -- current user from the bearer token.

**`POST /api/auth/logout`** -- records a `LOGOUT` audit event. JWTs are stateless in
this prototype, so logout is enforced client-side by discarding the token.

## Dashboard

**`GET /api/dashboard`** -- optional query params `region`, `category`, `risk_level`,
`date_from`, `date_to` (all filter the case-derived KPIs/charts). Returns 10 KPIs and
6 chart datasets (`cases_by_category`, `cases_over_time`, `network_activity_over_time`,
`entity_distribution`, `geographic_activity`, `alert_severity_distribution`), plus
recent alerts and the most-connected entities.

## Cases

**`GET /api/cases`** -- `search`, `status`, `category`, `priority`, `region`,
`risk_level`, `sort_by`, `sort_dir`, `page`, `page_size`.

**`GET /api/cases/{case_id}`** -- summary, description, related entities/locations,
timeline, evidence metadata, AI insights (top entities' connectivity scores within
this case's graph), alerts, and audit history referencing this case id. 404 if unknown.

## Entities

**`GET /api/entities`** -- `type` (PERSON/ORGANIZATION/VEHICLE/PHONE/LOCATION/ACCOUNT),
`q` (search), `page`, `page_size`.

**`GET /api/entities/{entity_id}`** -- full detail: attributes, connectivity score
(0-100) with an explicit `score_label`, an analytical observation with an
`insight_label` from the four-label vocabulary, raw centrality metrics, and recent
supporting evidence. 404 if unknown.

**`GET /api/entities/resolution/duplicates`** -- possible duplicate PERSON records
(never auto-merged; see `docs/AI_PIPELINE.md`).

## Graph

**`GET /api/graph/case/{case_id}`** -- Cytoscape.js-ready `{nodes, edges}` for every
relationship tagged to this case, plus detected communities and bridge-entity ids.

**`GET /api/graph/entity/{entity_id}?depth=1..3`** -- BFS outward from one entity.

## Alerts

**`GET /api/alerts`** -- `severity`, `entity_id`, `case_id`, `status`, `date_from`,
`date_to`.

**`PATCH /api/alerts/{alert_id}`** -- investigator/admin only. Body: any of
`{"status": "...", "assigned_to": "...", "note": "..."}`. Records an `ALERT_UPDATED`
audit event.

**`POST /api/alerts/run-detection`** -- investigator/admin only. Re-runs all 10
anomaly rules; clears and replaces alerts still in `NEW` status, preserves ones
already reviewed. Records a `DETECTION_RUN` audit event.

## Timeline / Locations

**`GET /api/timeline`** -- `case_id`, `entity_id`, `event_type`, `date_from`, `date_to`.

**`GET /api/locations`** -- `q`, `case_id`, `entity_id`, `date_from`, `date_to`.
Returns each location with an `activity_count` derived from relationships/events
referencing it (used to drive the map's activity heatmap coloring).

## Analysis

**`POST /api/analyze/text`** -- body `{"text": "...", "case_id": "optional"}`. Runs
the offline NLP extractor; returns structured entities and candidate relationship
"leads" (never persisted automatically). Records a `DATA_UPLOAD` audit event.

**`POST /api/analyze/network`** -- body `{"case_id": "..."}`. Full centrality +
community + bridge-entity breakdown for a case, independent of the graph endpoint's
Cytoscape-shaped response (this one is scores-first, for the "AI network analysis"
feature rather than the visual graph).

## Search

**`POST /api/search`** -- body `{"query": "...", "types": ["PERSON", ...] (optional)}`.
Searches cases and every entity table; returns id, label, type, related cases,
connection count, and last activity per result.

## Reports

**`POST /api/reports`** -- body `{"case_id": "...", "investigator_notes": "...",
"format": "json" | "pdf"}`. `format: "json"` returns the structured report body (case
information, network statistics, key relationships, timeline, alerts, geographic
summary, AI-assisted analytical observations, evidence references, investigator
notes, and a disclaimer); `format: "pdf"` streams a downloadable PDF with the same
content. Every report is prefixed with `"AI-Assisted Analytical Output — Requires
Investigator Verification"`. Records a `REPORT_GENERATED` audit event.

## Audit

**`GET /api/audit/logs`** -- investigator/admin only. `limit`, `event_type`.

**`GET /api/audit/verify`** -- investigator/admin only. Recomputes the SHA-256 hash
chain end to end; returns `{"verified": bool, "total_records", "records_checked",
"broken_at_seq", "message"}`.

## AI assistant

**`POST /api/assistant/ask`** -- body `{"question": "..."}`. Answers only from the
local dataset (case entities, an entity's strongest connections, entities spanning
multiple cases, why an entity was flagged, shared entities between two cases, or a
case's timeline summary). Returns `"No supporting information was found in the
available dataset."` when nothing matches, with supporting entity/event ids on every
data-backed answer.

## Health

**`GET /`** and **`GET /api/health`** -- no auth. Liveness/readiness checks.

## Error shape

FastAPI's default: `{"detail": "..."}` with the appropriate HTTP status
(400/401/403/404/422/429/500). 422 on request-body validation failures includes
per-field error detail from Pydantic.
