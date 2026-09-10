def test_path_between_connected_entities_returns_analytical_lead(client, auth_headers, seeded_database):
    rels = seeded_database["relationships"]
    edge = rels[0]
    response = client.post("/api/graph/path", json={"entity_a": edge["source_id"], "entity_b": edge["target_id"]}, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["paths"], "expected at least one path for two directly related entities"
    path = body["paths"][0]
    assert path["hop_count"] >= 1
    assert path["label"] == "Analytical lead — requires investigator verification"
    assert 0 <= path["confidence"] <= 1
    assert path["nodes"][0]["id"] == edge["source_id"]
    assert path["nodes"][-1]["id"] == edge["target_id"]


def test_path_between_unconnected_entities_reports_no_connection(client, auth_headers):
    response = client.post("/api/graph/path", json={"entity_a": "PERSON-999", "entity_b": "PERSON-998"}, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["paths"] == []
    assert "No connection was found" in body["message"]


def test_path_requires_authentication(client):
    response = client.post("/api/graph/path", json={"entity_a": "PERSON-101", "entity_b": "PERSON-102"})
    assert response.status_code == 401


def test_cross_case_compare_same_case_rejected(client, auth_headers):
    case_id = client.get("/api/cases?page_size=1", headers=auth_headers).json()["items"][0]["id"]
    response = client.post("/api/cross-case/compare", json={"case_id_a": case_id, "case_id_b": case_id}, headers=auth_headers)
    assert response.status_code == 400


def test_cross_case_compare_unknown_case_404(client, auth_headers):
    case_id = client.get("/api/cases?page_size=1", headers=auth_headers).json()["items"][0]["id"]
    response = client.post("/api/cross-case/compare", json={"case_id_a": case_id, "case_id_b": "CASE-9999"}, headers=auth_headers)
    assert response.status_code == 404


def test_cross_case_compare_returns_explainable_breakdown(client, auth_headers):
    cases = client.get("/api/cases?page_size=5", headers=auth_headers).json()["items"]
    response = client.post("/api/cross-case/compare", json={"case_id_a": cases[0]["id"], "case_id_b": cases[1]["id"]}, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert 0 <= body["similarity_score"] <= 100
    assert "shared_persons" in body["breakdown"]
    assert body["breakdown"]["temporal_similarity"] in {"LOW", "MEDIUM", "HIGH", "UNKNOWN"}
    assert body["label"] == "Analytical lead — requires investigator verification"
    assert "explanation" in body


def test_related_cases_endpoint_ranks_by_similarity(client, auth_headers):
    case_id = client.get("/api/cases?page_size=1", headers=auth_headers).json()["items"][0]["id"]
    response = client.get("/api/cross-case", params={"case_id": case_id}, headers=auth_headers)
    assert response.status_code == 200
    matches = response.json()["matches"]
    scores = [m["similarity_score"] for m in matches]
    assert scores == sorted(scores, reverse=True)
    assert all(m["case_id_a"] == case_id for m in matches)
