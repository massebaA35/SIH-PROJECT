# Database

## Engine

**SQLite** by default (`backend/crime_network.db`), zero setup. Every model uses
SQLAlchemy 2.0's dialect-agnostic column types, so switching to **PostgreSQL** for a
production-style deployment is a one-line change:

```bash
# backend/.env
DATABASE_URL=postgresql+psycopg2://ncrb:ncrb@localhost:5432/criminal_network
```

(add `psycopg2-binary` to `requirements.txt` first). No model or migration code
changes; `Base.metadata.create_all()` in `seed/seed_db.py` works against either engine.

## Tables

| Table | Purpose | Primary key |
|---|---|---|
| `users` | Auth accounts, bcrypt-hashed passwords, one of 3 roles | `USER-###` |
| `cases` | Investigation cases | `CASE-####` |
| `persons` | Person entities | `PERSON-###` |
| `organizations` | Organization entities | `ORG-###` |
| `vehicles` | Vehicle entities (synthetic plates) | `VEHICLE-###` |
| `phones` | Phone-number entities (synthetic numbers) | `PHONE-###` |
| `locations` | City-level location entities (lat/lng) | `LOC-###` |
| `accounts` | Synthetic financial-account entities (masked) | `ACCOUNT-###` |
| `relationships` | Graph edges between any two entities (or entity <-> case) | `REL-####` |
| `events` | Timeline events (calls, meetings, transactions, travel, ...) | `EVT-####` |
| `alerts` | Rule-based anomaly-detection results | `ALERT-####` |
| `evidence` | Evidence metadata (SHA-256 hash, type, source) | `EV-####` |
| `audit_logs` | Hash-chained, append-only audit trail | `seq` (auto-increment) |

## The entity-id convention

Every entity across all six entity tables uses a **globally unique, type-prefixed
string id** (`PERSON-101`, `VEHICLE-301`, `LOC-501`, ...), assigned once at seed time
and never reused. This is what lets `relationships.source_id`/`target_id` reference
*any* entity type without a polymorphic-association pattern or a discriminator
column: `app/services/entity_service.entity_type_from_id()` derives the type from the
id's prefix, and every relationship also carries its own `source_type`/`target_type`
as a denormalized convenience so graph queries never need a join back to six
different tables just to know what kind of node they're looking at.

## Relationships (edges)

```
relationships
├── id                REL-####
├── source_id / source_type
├── target_id / target_type
├── relation_type     KNOWS | CALLED | MET | WORKED_WITH | ASSOCIATED_WITH |
│                      TRAVELLED_TO | USED | TRANSFERRED_TO | LINKED_TO_CASE |
│                      ATTENDED | COMMUNICATED_WITH
├── case_id           which investigation this edge is recorded under (an edge
│                      can be duplicated under a second case_id -- see below)
├── occurred_on, frequency, confidence, evidence (free text), source
```

A single real-world link (e.g. two persons who met) can appear as **two separate
relationship rows with the same entities but different `case_id`s** when that link is
independently relevant to two investigations. This is deliberate, not a data-quality
bug: it's what makes "which entities appear in multiple cases" and "what connects
Case A to Case B" genuine, discoverable signals rather than something the seed data
has to fake with a join table. See `seed/generate_synthetic_data.py`'s
"duplicate-tag" step.

## Events vs. relationships

`events` and `relationships` overlap in what they represent (both can describe a
call, a meeting, a transfer) but serve different UI needs: `relationships` is the
graph's edge list (what the Network Analysis page renders), while `events` is a
flat, chronological log (what the Timeline page renders), with a `related_entities`
JSON array rather than a fixed source/target pair. They're generated together and
consistently in `seed/generate_synthetic_data.py` but are independent tables --
neither is derived from the other at read time.

## Audit chain schema

```
audit_logs
├── seq              auto-increment integer, the ordering (also the sequence
│                      number shown as e.g. "record #4" in a broken-chain report)
├── event_type        LOGIN | LOGIN_FAILED | LOGOUT | ALERT_UPDATED |
│                      DETECTION_RUN | DATA_UPLOAD | REPORT_GENERATED
├── user_id, username
├── event_data         canonical (sorted-key) JSON string of the event's details
├── timestamp
├── previous_hash       the current_hash of the row before this one (or 64 zeros
│                        for the very first row)
└── current_hash        SHA-256(previous_hash | event_type | event_data | timestamp)
```

See `docs/SECURITY.md` for what this buys you and its honest limits.

## Indexes

Every foreign-key-shaped column used in a hot filter path is indexed:
`relationships.source_id`, `relationships.target_id`, `relationships.case_id`,
`events.case_id`, `events.timestamp`, `alerts.case_id`, `alerts.entity_id`,
`alerts.timestamp`, `audit_logs.current_hash`, and `users.username` (unique). At the
prototype's data scale (hundreds to low thousands of rows per table) none of this is
load-bearing for performance, but it's the right shape to already have in place
before the dataset grows.

## Seeding

`seed/generate_synthetic_data.py` is a pure function (`generate() -> dict`) with no
database dependency, so it can be unit-tested and inspected standalone
(`python seed/generate_synthetic_data.py` prints record counts). `seed/seed_db.py`
is the thin layer that creates tables, hashes the three demo users' passwords, bulk-
inserts everything, and runs the anomaly detector once to seed initial alerts.
