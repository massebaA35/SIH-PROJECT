"""Tests for evidence document upload: hashing/dedup, per-type text
extraction, and error handling. PDF/docx fixtures are generated in-memory
rather than committed as binary files."""
from io import BytesIO

from docx import Document
from fpdf import FPDF

FIR_TEXT = (
    "The complainant, Person A, referred to as Arjun Nair, stated that his vehicle "
    "XX-00-AB-1234 was used without authorization. Records available to the "
    "investigating team indicate that Arjun Nair communicated with Person B, "
    "identified as Rahul Menon, on 15 October 2024."
)


def _fir_text(marker: str) -> str:
    """The test database is shared across this module's tests, and evidence
    dedup is keyed on the exact byte hash -- so each test that isn't
    specifically testing dedup needs its own distinct content to avoid
    colliding with another test's upload of the same FIR_TEXT."""
    return f"{FIR_TEXT} (ref: {marker})"


def _make_pdf_bytes(text: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 10, text)
    return bytes(pdf.output())


def _make_docx_bytes(text: str) -> bytes:
    doc = Document()
    doc.add_paragraph(text)
    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def _first_case_id(client, auth_headers) -> str:
    return client.get("/api/cases?page_size=1", headers=auth_headers).json()["items"][0]["id"]


def _upload(client, auth_headers, case_id, filename, content_bytes, content_type):
    return client.post(
        "/api/evidence/upload",
        headers=auth_headers,
        data={"case_id": case_id},
        files={"file": (filename, content_bytes, content_type)},
    )


def test_upload_txt_extracts_entities_and_records_evidence(client, auth_headers):
    case_id = _first_case_id(client, auth_headers)
    response = _upload(client, auth_headers, case_id, "fir.txt", _fir_text("txt").encode("utf-8"), "text/plain")

    assert response.status_code == 200
    body = response.json()
    assert body["case_id"] == case_id
    assert body["evidence_id"].startswith("EVID-")
    assert len(body["sha256_hash"]) == 64
    assert any(e["type"] == "PERSON" for e in body["entities"])

    case_detail = client.get(f"/api/cases/{case_id}", headers=auth_headers).json()
    evidence_ids = [e["id"] for e in case_detail["evidence"]]
    assert body["evidence_id"] in evidence_ids


def test_upload_pdf_extracts_text(client, auth_headers):
    case_id = _first_case_id(client, auth_headers)
    pdf_bytes = _make_pdf_bytes(_fir_text("pdf"))
    response = _upload(client, auth_headers, case_id, "fir.pdf", pdf_bytes, "application/pdf")

    assert response.status_code == 200
    body = response.json()
    assert any(e["type"] == "PERSON" for e in body["entities"])


def test_upload_docx_extracts_text(client, auth_headers):
    case_id = _first_case_id(client, auth_headers)
    docx_bytes = _make_docx_bytes(_fir_text("docx"))
    response = _upload(
        client, auth_headers, case_id, "fir.docx", docx_bytes,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    assert response.status_code == 200
    body = response.json()
    assert any(e["type"] == "PERSON" for e in body["entities"])


def test_reuploading_identical_bytes_is_rejected_as_duplicate(client, auth_headers):
    case_id = _first_case_id(client, auth_headers)
    content = _fir_text("dedup").encode("utf-8")
    first = _upload(client, auth_headers, case_id, "fir.txt", content, "text/plain")
    assert first.status_code == 200
    first_evidence_id = first.json()["evidence_id"]

    second = _upload(client, auth_headers, case_id, "fir-copy.txt", content, "text/plain")
    assert second.status_code == 409
    detail = second.json()["detail"]
    assert detail["evidence_id"] == first_evidence_id
    assert detail["case_id"] == case_id

    case_detail = client.get(f"/api/cases/{case_id}", headers=auth_headers).json()
    matching = [e for e in case_detail["evidence"] if e["id"] == first_evidence_id]
    assert len(matching) == 1, "a rejected duplicate upload must not create a second Evidence row"


def test_unsupported_extension_is_rejected(client, auth_headers):
    case_id = _first_case_id(client, auth_headers)
    response = _upload(client, auth_headers, case_id, "malware.exe", b"not a real document", "application/octet-stream")
    assert response.status_code == 400


def test_oversized_file_is_rejected(client, auth_headers):
    case_id = _first_case_id(client, auth_headers)
    oversized = b"a" * (2 * 1024 * 1024 + 1)
    response = _upload(client, auth_headers, case_id, "huge.txt", oversized, "text/plain")
    assert response.status_code == 400


def test_corrupt_pdf_is_rejected_as_unreadable(client, auth_headers):
    case_id = _first_case_id(client, auth_headers)
    response = _upload(client, auth_headers, case_id, "broken.pdf", b"%PDF-1.4 not actually a valid pdf stream", "application/pdf")
    assert response.status_code == 422

    case_detail = client.get(f"/api/cases/{case_id}", headers=auth_headers).json()
    assert not any(e["description"] == "broken.pdf" for e in case_detail["evidence"]), \
        "an unreadable upload must not create an Evidence row"


def test_unknown_case_404(client, auth_headers):
    response = _upload(client, auth_headers, "CASE-9999", "fir.txt", _fir_text("unknown-case").encode("utf-8"), "text/plain")
    assert response.status_code == 404


def test_upload_requires_investigator_role(client, analyst_token):
    case_id = client.get("/api/cases?page_size=1", headers={"Authorization": f"Bearer {analyst_token}"}).json()["items"][0]["id"]
    response = client.post(
        "/api/evidence/upload",
        headers={"Authorization": f"Bearer {analyst_token}"},
        data={"case_id": case_id},
        files={"file": ("fir.txt", _fir_text("rbac").encode("utf-8"), "text/plain")},
    )
    assert response.status_code == 403
