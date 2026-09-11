# Document Ingestion Pipeline — Design

Date: 2026-09-11
Status: Approved (pending user sign-off on this written spec)
Scope: `criminal-network-analysis/backend` and `criminal-network-analysis/frontend`

## Background

The brief's category A ("collect and process data from multiple sources") is
the one genuinely missing subsystem in this codebase. Categories B–E (entity
extraction, graph/network analytics, anomaly detection, investigator tools)
are already implemented to a high standard — see the gap analysis performed
earlier in this session. Today, "upload" in `Entities.tsx` is entirely
client-side: a `FileReader` reads a `.txt` file into browser memory and pastes
its contents into the same textarea used for typed statements. Nothing ever
reaches the backend as a file; no `Evidence` row is ever created outside of
seed data; there is no chain-of-custody hash computed at intake; PDFs and
`.docx` files are rejected outright.

This spec covers **v1 of real document ingestion**: uploading `.txt`, `.pdf`,
and `.docx` files as case evidence, extracting their text server-side,
hashing them for chain-of-custody and deduplication, persisting the original
file, and feeding the extracted text through the *existing* NLP extraction
pipeline unchanged. OCR for scanned documents and structured CDR/financial
CSV ingestion are explicitly out of scope for this pass (see Future Work).

## Goals

- An investigator can upload a real document file (not paste text) against a
  case and have it become a persisted, hash-verified piece of `Evidence`.
- The same document, uploaded twice (identical bytes), is detected and
  rejected rather than silently duplicated.
- Extraction/commit UX for the investigator is unchanged: they still see the
  entities/relationship-leads preview and explicitly commit it to the case
  graph, exactly as today.
- No regression to the existing paste-text flow, which remains a legitimate
  separate path (typed statements have no source document to preserve).

## Non-goals (this pass)

- OCR for scanned/image documents.
- Structured CSV ingestion (CDRs, bank transactions).
- Multilingual extraction.
- Editing/deleting previously uploaded Evidence.

## Architecture & data flow

1. Investigator opens a case, selects a file (`.txt`/`.pdf`/`.docx`) in the
   frontend, and submits it via `multipart/form-data` to
   `POST /api/evidence/upload` with `case_id` and the file.
2. Backend reads the raw bytes and computes `sha256(bytes)` **before** doing
   anything else — this is both the chain-of-custody fingerprint and the
   dedup key, computed on the untouched original, not on extracted text.
3. Backend queries `Evidence` for an existing row with that hash (across all
   cases, not just this one — the same document reappearing under a
   different case is exactly the kind of cross-case signal this system cares
   about, so it's surfaced, not hidden).
   - If found: return `409 Conflict` with the existing Evidence's `id` and
     `case_id` so the investigator can navigate to it. Nothing is stored or
     extracted.
4. If new: extract plain text by file type:
   - `.txt` → decode as UTF-8 (replace errors, matching a permissive
     investigator-facing tool rather than hard-failing on odd encodings).
   - `.pdf` → `pypdf.PdfReader`, concatenate `extract_text()` per page.
   - `.docx` → `python-docx`, concatenate paragraph text.
   - If extracted text is empty/whitespace-only (e.g. a scanned PDF with no
     text layer), return `422` with a message explaining OCR isn't
     supported yet, rather than silently proceeding with nothing to extract.
5. Save the original file to
   `./uploads/<case_id>/<evidence_id>_<original_filename>` on disk (path is
   sanitized: original filename is stripped to a safe basename before
   joining). Create the `Evidence` row (id, case_id, evidence_type="document",
   description=original filename, sha256_hash, source="Uploaded document",
   uploaded_by=current user, uploaded_at=now, plus a new `file_path` column).
6. Run the extracted text through the **existing, unmodified**
   `extract_entities` / `extract_rejected_candidates` /
   `extract_relationships_hint` functions from `ai/nlp_extraction.py` — this
   pipeline is not touched by this spec.
7. Record a `DATA_UPLOAD` audit event via the existing `record_event()`,
   extended with `evidence_id` and `sha256_hash` in its data payload.
8. Response mirrors `/api/analyze/text`'s shape (`entities`,
   `rejected_candidates`, `relationship_leads`, `summary`) plus `evidence_id`
   and `case_id`, so the frontend can feed the result straight into the
   existing review/commit UI, and separately record which Evidence backs
   this extraction (for future traceability from a committed entity back to
   its source document — not built in this pass, but the id is captured).
9. Committing extracted entities to the case graph continues to go through
   the existing, unmodified `POST /api/analyze/commit` →
   `extraction_commit_service.commit_extraction()` — this spec does not
   change that step.

## Components

**New:**
- `services/document_ingestion_service.py` — `extract_text_from_upload()`
  (dispatches by extension/content-type), `hash_bytes()`,
  `find_existing_evidence_by_hash()`, `store_uploaded_file()`,
  `create_evidence_record()`.
- `routers/evidence.py` — `POST /api/evidence/upload`
  (`Depends(require_investigator)`, matching the write-permission level
  already used by `/api/analyze/commit`).

**Extended:**
- `models/evidence.py` — add `file_path: Mapped[str]` column.
- `schemas/requests.py` — add `EvidenceUploadResponse`-shaped return typing
  (FastAPI response model; the file/case_id inputs arrive as `Form`/`File`
  params, not a Pydantic body, since this is multipart).
- `backend/requirements.txt` — add `pypdf` and `python-docx`.
- `main.py` — `app.include_router(evidence.router)`.
- `frontend/src/pages/Entities.tsx` — replace `handleFirFileUpload`'s
  client-side `FileReader`/`.txt`-only logic with an actual upload to
  `/evidence/upload`, passing the case id selected in the existing commit
  case-picker (the case must be chosen *before* upload now, since the
  backend needs it to store/associate Evidence — this reorders two fields
  already present in the UI but does not add new ones conceptually). The
  paste-text textarea path is untouched.

**Untouched (explicitly confirmed in this spec so implementers don't
"helpfully" touch them):**
- `ai/nlp_extraction.py`, `routers/analyze.py`,
  `services/extraction_commit_service.py`, `/api/analyze/text`,
  `/api/analyze/commit`.

## Data model change

```
Evidence.file_path: Mapped[str] = mapped_column(String(500), default="")
```

Existing seeded Evidence rows (synthetic demo data) have no backing file;
`file_path=""` for those, and the frontend/Evidence display already tolerates
a missing file (no download link is currently rendered anywhere for
Evidence — this spec does not add one, since there's no existing "view
original evidence file" UI to extend, and adding one is out of scope).

## Error handling

| Condition | Response |
|---|---|
| Unsupported extension (not txt/pdf/docx) | `400`, no storage, no Evidence row |
| File exceeds 2 MB | `400`, no storage (server-side enforcement of the limit the frontend already advertises) |
| SHA-256 already exists in `Evidence` | `409`, existing `evidence_id`/`case_id` returned, no storage |
| Extracted text empty (e.g. scanned PDF) | `422`, no storage, message states OCR is not yet supported |
| Corrupt/unparseable PDF or docx | `422`, no storage |
| `case_id` does not exist | `404` (mirrors existing `analyze_network`'s case-lookup behavior) |

In every rejection path, no `Evidence` row and no file are left behind —
storage and DB record creation happen only after extraction has already
succeeded, so there's never an orphaned Evidence pointing at an unreadable or
missing file.

## Testing

- `tests/test_document_ingestion.py` (new, mirroring the existing
  `tests/test_commit_extraction.py` pattern):
  - `.txt` upload → entities extracted, Evidence row created with correct hash.
  - `.pdf` upload (a small fixture PDF with known text) → same.
  - `.docx` upload (a small fixture docx) → same.
  - Re-uploading identical bytes → `409`, no second Evidence row.
  - Corrupt PDF bytes → `422`, no Evidence row created.
  - Empty-text PDF (image-only) → `422` with the OCR-not-supported message.
  - Unsupported extension (`.exe`) → `400`.
  - Oversized file → `400`.
- Manual verification: upload a real FIR-style `.pdf` and `.txt` through the
  running UI, confirm the entity/relationship preview renders identically to
  today's paste-text flow, confirm commit-to-case-graph still works
  unchanged, confirm the audit log shows the new `DATA_UPLOAD` event with
  `evidence_id`.

## Future work (explicitly deferred, not part of this spec)

- OCR pipeline for scanned/image PDFs.
- Structured CSV ingestion for CDRs and bank transaction records.
- Multilingual extraction.
- A "view/download original evidence file" UI backed by `file_path`.
- Composite per-entity risk scoring; geospatial co-location anomaly rule.
