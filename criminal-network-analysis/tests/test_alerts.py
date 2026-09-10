def test_alerts_list_and_all_carry_finding_labels(client, auth_headers):
    response = client.get("/api/alerts", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] > 0
    valid_labels = {"Potential connection", "Risk indicator", "Analytical lead", "Requires investigator verification"}
    for alert in body["items"]:
        assert alert["label"] in valid_labels
        assert alert["severity"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
        assert alert["status"] == "NEW"  # freshly seeded, none reviewed yet


def test_alerts_filter_by_severity(client, auth_headers):
    response = client.get("/api/alerts?severity=HIGH", headers=auth_headers)
    body = response.json()
    assert all(a["severity"] == "HIGH" for a in body["items"])


def test_alert_update_status_and_note(client, auth_headers):
    alert_id = client.get("/api/alerts", headers=auth_headers).json()["items"][0]["id"]
    response = client.patch(
        f"/api/alerts/{alert_id}",
        json={"status": "VERIFIED", "note": "Confirmed via independent evidence."},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "VERIFIED"
    assert body["notes"][-1]["text"] == "Confirmed via independent evidence."


def test_alert_update_not_found(client, auth_headers):
    response = client.patch("/api/alerts/ALERT-9999", json={"status": "VERIFIED"}, headers=auth_headers)
    assert response.status_code == 404


def test_anomaly_detection_rules_cover_all_ten_patterns(TestSessionLocal):
    """Every rule described in the brief (section G) must be able to fire
    against the seeded synthetic dataset -- otherwise the detector has a
    silent gap. See seed/generate_synthetic_data.py for the deliberately
    planted trigger patterns."""
    from app.analytics.anomaly_detection import run_all_rules
    db = TestSessionLocal()
    try:
        drafts = run_all_rules(db)
    finally:
        db.close()
    rules_fired = {d["detection_rule"] for d in drafts}
    expected_rules = {
        "unusual_communication_frequency", "sudden_communication_increase", "repeated_interactions",
        "financial_anomaly", "shared_vehicle_across_cases", "shared_phone_multiple_entities",
        "repeated_location_movement", "entities_shared_across_cases", "rapid_connectivity_change",
        "unusual_time_window_activity",
    }
    missing = expected_rules - rules_fired
    assert not missing, f"these anomaly rules never fired against the seeded dataset: {missing}"
