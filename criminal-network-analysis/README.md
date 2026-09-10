# AI-Powered Criminal Network Analysis System

**Ministry of Home Affairs · National Crime Records Bureau · Women Safety Division**
Smart India Hackathon prototype — Theme: Blockchain & Cybersecurity

An investigative decision-support platform. It analyzes structured and unstructured
crime-related data to help authorized investigators discover hidden relationships,
network structures, high-influence entities, suspicious activity patterns, and
connections between cases — using only synthetic, fictional data.

**This system is not, and must never be treated as, a guilt-detection tool.** Every
AI-generated finding is presented as one of four labels — *Potential connection*,
*Risk indicator*, *Analytical lead*, or *Requires investigator verification* — never
as a determination of criminal status. See [docs/SECURITY.md](docs/SECURITY.md) and
[docs/AI_PIPELINE.md](docs/AI_PIPELINE.md) for how that constraint is enforced in code.

---

## 1. Prerequisites

- **Python 3.11+** (developed and tested on 3.14)
- **Node.js 18+** and npm (developed and tested on Node 24 / npm 11)
- No paid APIs, no external services, and no internet connection are required once
  dependencies are installed — the app runs entirely on local SQLite and a local,
  rule-based/offline AI layer.

## 2. Installation

```bash
cd criminal-network-analysis

# --- Backend ---
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt

# --- Frontend (separate terminal) ---
cd ../frontend
npm install
```

## 3. Environment variables

Copy the example env files and adjust if needed. Both ship with safe local defaults,
so this step is optional for a first run.

```bash
# backend/.env.example -> backend/.env
# frontend/.env.example -> frontend/.env.local
```

Never commit a real `.env` file. See [backend/.env.example](backend/.env.example) and
[frontend/.env.example](frontend/.env.example) for every variable and what it controls.

> **Port note:** the frontend dev server runs on **5180** (not Vite's default 5173) and
> the backend examples below use **8010** (not the more common 8000). Both were chosen
> deliberately so this project doesn't collide with another local service that may
> already be using the usual ports. If you use different ports, keep three things in
> sync: the `--port` you pass to `uvicorn`, `VITE_API_BASE_URL` in `frontend/.env.local`,
> and `CORS_ORIGINS` in `backend/.env` (or `backend/app/config.py`'s default).

## 4. Database setup

No separate database server is required. The prototype uses **SQLite** by default
(`backend/crime_network.db`, created automatically). SQLAlchemy models live in
`backend/app/models/`; see [docs/DATABASE.md](docs/DATABASE.md) for the full schema
and the PostgreSQL connection string to use instead for a production-style deployment.

## 5. Seed data

Generates and loads a synthetic, interconnected dataset (50 persons, 10 organizations,
30 vehicles, 50 phone records, 20 locations, 15 accounts, 20 cases, 100+ events, 370+
relationships across 5 detectable communities with deliberate bridge entities) and runs
the rule-based anomaly detector to seed initial alerts.

```bash
cd backend
python -m seed.seed_db --reset
```

Run it again with `--reset` any time you want a clean slate; without `--reset` it
refuses to reseed a non-empty database. `python seed/generate_synthetic_data.py` alone
(no DB needed) prints the record counts it would generate, useful for a quick sanity
check.

## 6. Start the backend

```bash
cd backend
uvicorn app.main:app --reload --port 8010
```

- Health check: `curl http://localhost:8010/api/health`
- Interactive API docs (Swagger UI): `http://localhost:8010/docs`
- Alternate API docs (ReDoc): `http://localhost:8010/redoc`

## 7. Start the frontend

```bash
cd frontend
npm run dev
```

Open `http://localhost:5180`. The dev server proxies nothing — it calls the backend
directly at `VITE_API_BASE_URL` (see `frontend/.env.local`), so the backend must
already be running.

## 8. Demo login

Three demo accounts are created by the seed script — **prototype credentials only,
never reuse or expose these in a real deployment:**

| Role | Username | Password |
|---|---|---|
| Administrator | `admin.demo` | `AdminDemo@123` |
| Investigator | `investigator.demo` | `InvestigatorDemo@123` |
| Analyst | `analyst.demo` | `AnalystDemo@123` |

Analysts can read all investigative data but cannot update alerts or view audit logs;
Investigators and Administrators can do both. See [docs/SECURITY.md](docs/SECURITY.md)
for the full RBAC matrix.

## 9. API documentation

FastAPI generates interactive documentation automatically from the route/schema
definitions — no separate doc-build step. With the backend running:

- Swagger UI: `http://localhost:8010/docs`
- ReDoc: `http://localhost:8010/redoc`
- OpenAPI JSON: `http://localhost:8010/openapi.json`

A hand-written endpoint reference with example requests/responses is also in
[docs/API.md](docs/API.md).

## 10. Troubleshooting

- **"Only one usage of each socket address..." / `EADDRINUSE`** — something else is
  already listening on the port you asked for (this happened during development: a
  different local prototype was already on `:8000`). Pick a free port with `--port`
  on the `uvicorn` command, and update `VITE_API_BASE_URL` and `CORS_ORIGINS` to match.
- **CORS error in the browser console** (`No 'Access-Control-Allow-Origin' header...`)
  — the frontend's origin isn't in the backend's `CORS_ORIGINS`. Add it (comma-separated)
  in `backend/.env`, or match the frontend's port to one of the defaults in
  `backend/app/config.py`.
- **401 on every request after logging in** — the JWT expired
  (`ACCESS_TOKEN_EXPIRE_MINUTES`, default 60) or `JWT_SECRET_KEY` changed since the
  token was issued (e.g. you edited `.env` mid-session). Log in again.
- **`ModuleNotFoundError: No module named 'scipy'`** — `networkx`'s PageRank
  implementation needs `scipy`; it's in `requirements.txt`, so re-run
  `pip install -r requirements.txt` inside the activated venv.
- **Passlib/bcrypt warning on startup** — harmless version-compatibility noise from
  `passlib` reading `bcrypt.__about__`; login still works. Pinning `bcrypt==4.0.1` (as
  `requirements.txt` does) avoids it entirely.
- **Windows PDF/report generation crashes on a dash or curly quote** — already handled:
  `app/services/report_service.py` sanitizes report text for the PDF's Latin-1-only
  core font before rendering. If you add new report content with other Unicode
  punctuation, extend `_PDF_CHAR_MAP` there.
- **Frontend shows blank pages / stale data** — hard-refresh, and confirm the backend
  is actually running and reachable at `VITE_API_BASE_URL` (check the Network tab).
- **Want to start over** — delete `backend/crime_network.db` and re-run
  `python -m seed.seed_db --reset`.

---

## Project layout

```
criminal-network-analysis/
├── backend/          FastAPI + SQLAlchemy + SQLite, graph analytics, AI layer, tests
├── frontend/          React + TypeScript + Vite + Tailwind + Cytoscape.js
├── database/          Schema reference (see docs/DATABASE.md)
├── docs/              ARCHITECTURE, API, DATABASE, SECURITY, AI_PIPELINE, DEMO_GUIDE
├── docker-compose.yml
└── .env.example
```

## Further reading

- [docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md) — the exact click-through path for an SIH demo
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system design and module layout
- [docs/API.md](docs/API.md) — endpoint reference
- [docs/DATABASE.md](docs/DATABASE.md) — schema and entity-relationship notes
- [docs/SECURITY.md](docs/SECURITY.md) — auth, RBAC, hardening, and the audit hash chain
- [docs/AI_PIPELINE.md](docs/AI_PIPELINE.md) — the full ingestion → analytics pipeline
  and why every stage is explainable and offline

## What is and isn't real here

Everything in this repository — names, phone numbers, plate numbers, account numbers,
addresses, and events — is **synthetic and fictional**, generated by
`backend/seed/generate_synthetic_data.py`. Nothing here is production-hardened as-is:
the JWT secret, database, and rate limits are prototype defaults meant for local
evaluation, not a real deployment. See [docs/SECURITY.md](docs/SECURITY.md) for exactly
what would need to change before this touched real data.
