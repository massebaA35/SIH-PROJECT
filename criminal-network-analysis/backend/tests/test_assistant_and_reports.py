def test_assistant_answers_case_entities_question(client, auth_headers):
    case_id = client.get("/api/cases?page_size=1", headers=auth_headers).json()["items"][0]["id"]
    response = client.post("/api/assistant/ask", json={"question": f"What entities are connected to {case_id}?"}, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert case_id in body["answer"]
    assert "Requires Investigator Verification" in body["disclaimer"]


def test_assistant_no_data_response_for_unknown_case(client, auth_headers):
    response = client.post("/api/assistant/ask", json={"question": "What entities are connected to CASE-9999?"}, headers=auth_headers)
    body = response.json()
    assert body["answer"] == "No supporting information was found in the available dataset."


def test_assistant_why_flagged(client, auth_headers):
    alert = client.get("/api/alerts", headers=auth_headers).json()["items"][0]
    response = client.post("/api/assistant/ask", json={"question": f"Why is {alert['entity_id']} flagged?"}, headers=auth_headers)
    body = response.json()
    assert alert["id"] in body["supporting"]


def test_report_json_labels_ai_output(client, auth_headers):
    case_id = client.get("/api/cases?page_size=1", headers=auth_headers).json()["items"][0]["id"]
    response = client.post("/api/reports", json={"case_id": case_id, "format": "json"}, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["report_label"] == "AI-Assisted Analytical Output — Requires Investigator Verification"
    assert "disclaimer" in body


def test_report_not_found_for_unknown_case(client, auth_headers):
    response = client.post("/api/reports", json={"case_id": "CASE-9999", "format": "json"}, headers=auth_headers)
    assert response.status_code == 404


def test_report_pdf_downloads(client, auth_headers):
    case_id = client.get("/api/cases?page_size=1", headers=auth_headers).json()["items"][0]["id"]
    response = client.post("/api/reports", json={"case_id": case_id, "format": "pdf"}, headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"


def test_search_returns_matching_entities(client, auth_headers):
    response = client.post("/api/search", json={"query": "PERSON-101"}, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert any(r["id"] == "PERSON-101" for r in body["results"])


def test_timeline_filters_by_case(client, auth_headers):
    case_id = client.get("/api/cases?page_size=1", headers=auth_headers).json()["items"][0]["id"]
    response = client.get(f"/api/timeline?case_id={case_id}", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert all(item["case_id"] == case_id for item in body["items"])


def test_locations_endpoint_returns_seeded_locations(client, auth_headers):
    response = client.get("/api/locations", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    for loc in body["items"]:
        assert -90 <= loc["latitude"] <= 90
        assert -180 <= loc["longitude"] <= 180


def test_dashboard_kpis_present(client, auth_headers):
    response = client.get("/api/dashboard", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body["kpis"]) == 10
    assert set(body["charts"].keys()) == {
        "cases_by_category", "cases_over_time", "network_activity_over_time",
        "entity_distribution", "geographic_activity", "alert_severity_distribution",
    }
