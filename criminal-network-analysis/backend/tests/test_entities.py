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
