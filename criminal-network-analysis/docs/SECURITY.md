# Security

## Authentication

- **JWT** (HS256, `python-jose`), issued on `POST /api/auth/login`, 60-minute expiry
  by default (`ACCESS_TOKEN_EXPIRE_MINUTES`). Stateless: there is no server-side
  session or token blacklist in this prototype, so "logout" is enforced client-side
  by discarding the token (still recorded as a `LOGOUT` audit event).
- **Password hashing:** bcrypt via `passlib`. Plaintext passwords are never stored or
  logged; `app/security/auth.py`'s `hash_password`/`verify_password` are the only two
  functions that touch a password.
- **Demo credentials only.** The three seeded accounts (`admin.demo`,
  `investigator.demo`, `analyst.demo`) are for local evaluation. Nothing in this repo
  hard-codes a production secret -- `JWT_SECRET_KEY` in `.env.example` is a visibly
  fake placeholder with a comment telling you to generate a real one before any real
  deployment.

## Role-based access control

Three roles: `ADMINISTRATOR`, `INVESTIGATOR`, `ANALYST`. Enforced with FastAPI
dependencies in `app/security/rbac.py`:

| Capability | Administrator | Investigator | Analyst |
|---|:---:|:---:|:---:|
| Read cases, entities, graph, timeline, map, search, AI assistant | Yes | Yes | Yes |
| Generate reports | Yes | Yes | Yes |
| Update/review alerts, re-run detection | Yes | Yes | No (403) |
| View audit logs / verify the hash chain | Yes | Yes | No (403) |

`require_roles(*roles)` is a small dependency factory; every router that needs
write access or audit visibility depends on `require_investigator` (Admin +
Investigator) instead of re-checking `user.role` inline, so the policy lives in one
place. `tests/test_auth.py` and `tests/test_audit.py` assert the 403s directly.

## Input validation

Every request body is a Pydantic model (`app/schemas/`) with explicit length/pattern
constraints (e.g. `AlertUpdateRequest.status` is a regex-constrained enum, not a free
string). FastAPI rejects anything that doesn't match with a 422 before it reaches
application code. Query parameters use the same mechanism via `fastapi.Query(...)`.

## CORS

Configured via `CORS_ORIGINS` (comma-separated) in `app/config.py`, defaulting to the
frontend's dev-server origins only (`http://localhost:5180` and the Vite default
`:5173`, both `localhost` and `127.0.0.1`). Not a wildcard `*`.

## Rate limiting

A lightweight in-memory sliding-window limiter (`app/main.py`'s `rate_limit`
middleware), default 120 requests/minute per client IP, returns 429 over the limit.
This is adequate for a single-process prototype; a multi-worker production deployment
would move this to Redis or an API gateway (noted in the code comment).

## Secure HTTP headers

`app/main.py`'s `security_headers` middleware sets `X-Content-Type-Options: nosniff`,
`X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, and a `Content-Security-Policy:
default-src 'self'` on every response.

## SQL injection / XSS

- **SQL injection:** every query goes through SQLAlchemy's ORM query builder with
  bound parameters -- there is no raw, string-interpolated SQL anywhere in the
  codebase.
- **XSS:** the frontend is React, which escapes all interpolated text by default;
  nothing in the app uses `dangerouslySetInnerHTML`.

## Environment variables / no secrets in source

`backend/.env.example` and `frontend/.env.example` document every variable; real
`.env`/`.env.local` files are git-ignored (`.gitignore` at the repo root). The default
`JWT_SECRET_KEY` is an obviously-fake placeholder string, never a real secret.

## Audit logging

Every login (success and failure), logout, alert update, detection run, text-analysis
request, and report generation writes an audit record via
`app/security/audit_chain.record_event`. See below for the tamper-evidence guarantee.

## Blockchain-inspired tamper-evident audit trail

Each `audit_logs` row's `current_hash` is:

```
SHA-256(previous_hash | event_type | canonical_json(event_data) | timestamp)
```

Because every record commits to the hash of the one immediately before it, changing
any field of any historical record -- or deleting one -- changes that record's
recomputed hash and breaks the chain for every record after it.
`GET /api/audit/verify` recomputes the whole chain from the genesis hash (64 zeros)
and reports exactly which record first fails to match (`tests/test_audit.py::
test_hash_chain_detects_tampering` demonstrates this directly by mutating a row and
re-verifying).

**What this honestly is:** a single-writer, append-only SHA-256 hash chain in a
regular SQL table. **What it is not:** a distributed ledger, a consensus protocol, or
tamper-*proof* against someone with direct database write access and the ability to
recompute and overwrite every subsequent hash too (a determined attacker with full DB
access could rewrite the whole chain consistently). The value it provides is
detecting *accidental or unsophisticated* tampering, and making *any* tampering
attempt leave a cryptographically detectable trace rather than a silent edit.

`app/security/audit_chain.py`'s docstring calls this out explicitly, and the
Architecture doc notes the migration path: because `record_event`/`verify_chain` are
the only two functions any other code calls, replacing the SQLite-backed chain with a
real permissioned ledger client (Hyperledger Fabric, or similar) means reimplementing
those two functions and nothing else.

## What would need to change before touching real data

This is a prototype's honest checklist, not a criticism of the current state:

1. Generate and set a real, secret `JWT_SECRET_KEY` (never the placeholder).
2. Move from SQLite to PostgreSQL with proper backup/replication.
3. Add refresh tokens and/or a server-side revocation list instead of relying purely
   on short-lived access tokens.
4. Move the rate limiter to a shared store (Redis) for multi-worker deployments.
5. Put the audit hash chain behind write-once storage or a real permissioned ledger.
6. Add structured request logging and monitoring/alerting infrastructure.
7. Run a real threat model and pen test before any exposure to non-synthetic data.
