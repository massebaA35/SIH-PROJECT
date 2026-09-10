def test_login_writes_audit_record(client, auth_headers):
    response = client.get("/api/audit/logs?limit=50", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert any(item["event_type"] == "LOGIN" for item in body["items"])


def test_audit_verify_passes_on_untampered_chain(client, auth_headers):
    response = client.get("/api/audit/verify", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["verified"] is True
    assert body["broken_at_seq"] is None


def test_audit_requires_investigator_role(client, analyst_token):
    response = client.get("/api/audit/logs", headers={"Authorization": f"Bearer {analyst_token}"})
    assert response.status_code == 403


def test_hash_chain_detects_tampering(TestSessionLocal, client, auth_headers):
    # generate at least one real record via the API first
    client.get("/api/audit/logs", headers=auth_headers)

    from app.models.audit import AuditLog
    from app.security.audit_chain import verify_chain

    db = TestSessionLocal()
    try:
        first = db.query(AuditLog).order_by(AuditLog.seq.asc()).first()
        assert first is not None
        original_event_data = first.event_data
        first.event_data = original_event_data.replace("investigator", "TAMPERED")
        db.commit()

        result = verify_chain(db)
        assert result["verified"] is False
        assert result["broken_at_seq"] == first.seq

        # restore, to avoid bleeding a broken chain into later tests
        first.event_data = original_event_data
        db.commit()
        assert verify_chain(db)["verified"] is True
    finally:
        db.close()


def test_hash_chain_links_records_sequentially(TestSessionLocal):
    from app.models.audit import AuditLog
    from app.security.audit_chain import record_event, GENESIS_HASH

    db = TestSessionLocal()
    try:
        first = record_event(db, "TEST_EVENT_A", {"note": "first"})
        second = record_event(db, "TEST_EVENT_B", {"note": "second"})
        assert second.previous_hash == first.current_hash
        if db.query(AuditLog).count() == 2:
            assert first.previous_hash == GENESIS_HASH
    finally:
        db.close()
