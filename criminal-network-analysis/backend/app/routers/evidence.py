"""Evidence intake: upload a document as case evidence, hashed for chain of
custody and deduplication, then run through the same offline NLP extraction
pipeline that /api/analyze/text uses -- extraction is preview-only here too;
/api/analyze/commit is still the explicit step that writes entities and
relationships into the case network graph."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.ai.nlp_extraction import extract_entities, extract_rejected_candidates, extract_relationships_hint
from app.database import get_db
from app.models.case import Case
from app.models.user import User
from app.security.audit_chain import record_event
from app.security.rbac import require_investigator
from app.services.document_ingestion_service import (
    DuplicateEvidence, FileTooLarge, UnreadableDocument, UnsupportedFileType, ingest_document,
)

router = APIRouter(prefix="/api/evidence", tags=["evidence"])


@router.post("/upload")
async def upload_evidence(
    case_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_investigator),
):
    if not db.get(Case, case_id):
        raise HTTPException(404, "Case not found")

    data = await file.read()
    try:
        result = ingest_document(db, case_id, file.filename or "upload", data, uploaded_by=user.username)
    except UnsupportedFileType as exc:
        raise HTTPException(400, str(exc)) from exc
    except FileTooLarge as exc:
        raise HTTPException(400, str(exc)) from exc
    except DuplicateEvidence as exc:
        raise HTTPException(409, {
            "message": "This document is already recorded as evidence.",
            "evidence_id": exc.evidence_id,
            "case_id": exc.case_id,
        }) from exc
    except UnreadableDocument as exc:
        raise HTTPException(422, str(exc)) from exc

    text = result["text"]
    entities = extract_entities(text)
    rejected = extract_rejected_candidates(text)
    relationship_leads = extract_relationships_hint(text, entities)
    duplicate_relationships_removed = sum(max(0, lead["mention_count"] - 1) for lead in relationship_leads)

    record_event(
        db, "DATA_UPLOAD",
        {
            "case_id": case_id, "evidence_id": result["evidence_id"], "sha256_hash": result["sha256_hash"],
            "filename": file.filename, "entities_found": len(entities),
        },
        user_id=user.id, username=user.username,
    )

    return {
        "evidence_id": result["evidence_id"],
        "case_id": case_id,
        "sha256_hash": result["sha256_hash"],
        "entities": entities,
        "rejected_candidates": rejected,
        "relationship_leads": relationship_leads,
        "summary": {
            "entities_extracted": len(entities),
            "valid_entities": len(entities),
            "rejected_candidates": len(rejected),
            "duplicate_relationships_merged": duplicate_relationships_removed,
        },
        "disclaimer": (
            "Entities and relationships extracted from uploaded evidence are analytical leads only "
            "and require investigator verification before being added to the case record."
        ),
    }
