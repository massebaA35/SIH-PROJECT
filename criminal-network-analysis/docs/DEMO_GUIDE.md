# Demo guide

A ~8-10 minute walkthrough covering every acceptance-criteria feature, in the order
the brief describes as the natural investigator workflow.

## Before you start

1. Backend running: `uvicorn app.main:app --reload --port 8010` (from `backend/`,
   venv activated).
2. Database seeded: `python -m seed.seed_db --reset` (from `backend/`) -- do this
   once before the demo so the numbers below match what you'll actually see.
3. Frontend running: `npm run dev` (from `frontend/`), open `http://localhost:5180`.

## 1. Login

Sign in as **`investigator.demo` / `InvestigatorDemo@123`** (click the demo-account
row on the login page to auto-fill it). Point out the two other roles listed
(Administrator, Analyst) and that Analysts can view everything but can't touch alerts
or audit logs -- switch accounts later to show the 403 if asked.

## 2. Dashboard

Lands on `/dashboard`. Point out:
- The 10 KPI cards (active cases, persons of interest, organizations, vehicles,
  locations, phone numbers, financial entities, detected relationships, suspicious
  activities, high-priority alerts) -- all real counts from the seeded dataset, not
  placeholders.
- Six charts: cases by category, cases over time, entity distribution, alert severity
  distribution, geographic activity, network activity over time.
- The region/risk-level filters at the top-right actually re-query the backend.
- The "Priority alerts" panel already shows `FindingLabel` badges
  (*Analytical lead* / *Risk indicator* / ...) next to severity -- call out that no
  alert here is phrased as an accusation.

## 3. Search a case, open it

Use the top-bar global search or go to `/cases`. Filter/sort/search live against the
backend (debounced). Open any case -- note the tabs: Overview (network graph + AI
insights), Entities, Timeline, Evidence, Audit.

On the Overview tab, the **embedded network graph** already renders; the "AI
analytical observations" panel on the right shows differentiated connectivity scores
(not everyone at 100 -- point out two different entities with two different scores)
each tagged with a finding label and a plain-language reason.

## 4. Network Analysis -- the centerpiece

Click "Open full analysis" (or the sidebar's Network Analysis). This is the main
feature:
- **Search** an entity in the graph search box; watch nodes filter live.
- **Toggle node-type filters** (PERSON/ORGANIZATION/VEHICLE/...) -- the graph
  re-renders with only the selected types.
- **Expand the relationship-type filters** panel (11 types) and toggle a few off.
- **"Color by community"** -- switch between coloring by entity type and by detected
  community; watch the same graph resolve into visually distinct clusters.
- **"Highlight highly connected"** -- highlights the top quartile of nodes by
  connection count.
- **Shortest path finder** -- pick two entities from the dropdowns, click "Highlight
  path"; the path lights up on the graph.
- Click any node -> the right-side "Node details" panel loads that entity's real
  score and analytical observation without leaving the page.
- Point out the **Communities** and **Potential bridge entities** panels on the
  right -- bridge entities are explicitly labeled *Analytical lead*, never "leader."

## 5. Entity profile

Click through to a full entity page (`/entities/:id`). Show the connectivity score,
its label, the metrics grid (degree/betweenness/closeness centrality, PageRank), the
supporting-evidence list with per-item confidence, and the mini network view. Click
"Open in analysis" to jump back into the full graph centered on this entity.

## 6. AI investigation assistant

Use the global search bar, or open a terminal/`curl`/Swagger UI (`/docs`) against
`POST /api/assistant/ask` live, and ask a few of the example questions from the
brief:
- *"What entities are connected to CASE-1001?"*
- *"Show the strongest connections of PERSON-101."*
- *"Which entities appear in multiple cases?"*
- *"Why is PERSON-101 flagged?"*
- *"What connections exist between CASE-1001 and CASE-1005?"*
- *"Summarize the activity timeline for CASE-1001."*

Then ask something not in the dataset (e.g. *"What entities are connected to
CASE-9999?"*) and show the exact required fallback: *"No supporting information was
found in the available dataset."* -- proving it never fabricates an answer.

## 7. Timeline

`/timeline`. Filter by case, event type, and date range; click an event to see its
detail panel including linked entities.

## 8. Geospatial

`/map`. Point out the activity-intensity coloring (low/moderate/high), marker
clustering as you zoom out, and the disclaimer that coordinates are city-level only
-- never a real private address.

## 9. Alerts

`/alerts`. Filter by severity/status/case. Open an alert, show the evidence text
(the specific numbers the rule observed, not a bare "suspicious" flag), change its
status through the workflow (`NEW -> UNDER_REVIEW -> VERIFIED`/`DISMISSED`), assign
it to an investigator, add a note. Mention "Re-run detection" re-executes all ten
rules live.

## 10. Generate a report

`/reports`, pick the same case from step 3, add an investigator note, click "Generate
report" -- walk through the on-screen structured report (case info, network stats, AI
observations, key relationships, alerts, evidence references, disclaimer), then click
"Download PDF" to show the exported file opens and is properly labeled
*"AI-Assisted Analytical Output — Requires Investigator Verification"* on page one.

## 11. Audit integrity

`/audit`. Show the chain-verification banner ("Audit chain intact"), then --
optionally, for a stronger demo -- open a Python shell and directly edit one
`audit_logs.event_data` value in the SQLite file, refresh the page, and show the
banner flips to "Chain integrity broken at record #N." Restore it (re-seed, or edit
it back) afterward.

## Close

Land back on the Dashboard and reiterate the one sentence that matters most for the
judges: **every AI-generated finding in this system carries one of four explicit
labels -- Potential connection, Risk indicator, Analytical lead, or Requires
investigator verification -- and none of them, anywhere in the codebase, asserts
guilt.**
