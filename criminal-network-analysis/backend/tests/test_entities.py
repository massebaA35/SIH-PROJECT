def test_list_entities_meets_minimum_dataset_scale(client, auth_headers):
    persons = client.get("/api/entities?type=PERSON&page_size=1", headers=auth_headers).json()
    orgs = client.get("/api/entities?type=ORGANIZATION&page_size=1", headers=auth_headers).json()
    vehicles = client.get("/api/entities?type=VEHICLE&page_size=1", headers=auth_headers).json()
    phones = client.get("/api/entities?type=PHONE&page_size=1", headers=auth_headers).json()

    assert persons["total"] >= 50
    assert orgs["total"] >= 10
    assert vehicles["total"] >= 30
    assert phones["total"] >= 50


def test_entity_search_by_query(client, auth_headers):
    response = client.get("/api/entities?q=PERSON-101", headers=auth_headers)
    body = response.json()
    assert any(item["id"] == "PERSON-101" for item in body["items"])


def test_entity_detail_not_found(client, auth_headers):
    response = client.get("/api/entities/PERSON-9999", headers=auth_headers)
    assert response.status_code == 404


def test_entity_detail_carries_finding_label(client, auth_headers):
    response = client.get("/api/entities/PERSON-101", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["insight_label"] in ("Potential connection", "Risk indicator", "Analytical lead", "Requires investigator verification")
    assert 0 <= body["score"] <= 100


def test_entity_scores_are_differentiated(client, auth_headers):
    """Regression test: entity connectivity scores must not all collapse to
    100, which happened when an entity was scored against a 1-hop star
    graph centered on itself (see app/routers/entities.py)."""
    scores = set()
    for entity_id in ("PERSON-101", "PERSON-105", "VEHICLE-301", "ACCOUNT-601"):
        response = client.get(f"/api/entities/{entity_id}", headers=auth_headers)
        scores.add(response.json()["score"])
    assert len(scores) > 1, f"expected differentiated scores, got {scores}"


def test_entity_resolution_never_auto_merges(client, auth_headers):
    response = client.get("/api/entities/resolution/duplicates", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    for candidate in body["candidates"]:
        assert "recommendation" in candidate
        assert "verification" in candidate["recommendation"].lower()


def test_entity_resolution_candidates_expose_indicator_breakdown(client, auth_headers):
    response = client.get("/api/entities/resolution/duplicates", headers=auth_headers)
    body = response.json()
    assert body["candidates"], "expected at least one duplicate candidate from the synthetic dataset"
    for candidate in body["candidates"]:
        indicators = candidate["indicators"]
        for key in ("name_similarity", "phone_overlap", "location_overlap", "organization_overlap"):
            assert 0 <= indicators[key] <= 1


def test_entity_resolution_decision_is_recorded_in_audit_log(client, auth_headers):
    candidates = client.get("/api/entities/resolution/duplicates", headers=auth_headers).json()["candidates"]
    pair = candidates[0]
    response = client.post("/api/entities/resolution/decision", headers=auth_headers, json={
        "entity_a": pair["entity_a"]["id"], "entity_b": pair["entity_b"]["id"], "decision": "DISMISSED",
    })
    assert response.status_code == 200
    assert response.json()["decision"] == "DISMISSED"

    audit_response = client.get("/api/audit/logs", headers=auth_headers, params={"limit": 5})
    events = audit_response.json()["items"]
    assert any(e["event_type"] == "ENTITY_RESOLUTION_DECISION" for e in events)


def test_entity_resolution_decision_rejects_invalid_value(client, auth_headers):
    response = client.post("/api/entities/resolution/decision", headers=auth_headers, json={
        "entity_a": "PERSON-101", "entity_b": "PERSON-102", "decision": "MERGED",
    })
    assert response.status_code == 422
