def test_list_cases_returns_seeded_dataset(client, auth_headers):
    response = client.get("/api/cases", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 20  # brief requires "at least 20 cases"
    assert len(body["items"]) <= body["page_size"]


def test_list_cases_pagination(client, auth_headers):
    page1 = client.get("/api/cases?page=1&page_size=5", headers=auth_headers).json()
    page2 = client.get("/api/cases?page=2&page_size=5", headers=auth_headers).json()
    assert len(page1["items"]) == 5
    assert {i["id"] for i in page1["items"]}.isdisjoint({i["id"] for i in page2["items"]})


def test_list_cases_filter_by_status(client, auth_headers):
    response = client.get("/api/cases?status=Active", headers=auth_headers)
    body = response.json()
    assert all(item["status"] == "Active" for item in body["items"])


def test_list_cases_search(client, auth_headers):
    all_cases = client.get("/api/cases?page_size=100", headers=auth_headers).json()["items"]
    target = all_cases[0]
    response = client.get(f"/api/cases?search={target['id']}", headers=auth_headers)
    body = response.json()
    assert any(item["id"] == target["id"] for item in body["items"])


def test_case_detail_not_found(client, auth_headers):
    response = client.get("/api/cases/CASE-9999", headers=auth_headers)
    assert response.status_code == 404


def test_case_detail_shape(client, auth_headers):
    case_id = client.get("/api/cases?page_size=1", headers=auth_headers).json()["items"][0]["id"]
    response = client.get(f"/api/cases/{case_id}", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    for key in ("case", "related_entities", "related_events", "timeline", "ai_insights", "alerts", "audit_history"):
        assert key in body


def test_cases_require_auth(client):
    response = client.get("/api/cases")
    assert response.status_code == 401
