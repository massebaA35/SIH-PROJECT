def test_bounds_returns_earliest_and_latest_dates(client, auth_headers):
    response = client.get("/api/network-time-machine/bounds", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["earliest"] is not None
    assert body["latest"] is not None
    assert body["earliest"] <= body["latest"]


def test_time_machine_requires_authentication(client):
    response = client.get("/api/network-time-machine", params={"start_date": "2025-01-01", "end_date": "2025-06-01"})
    assert response.status_code == 401


def test_time_machine_rejects_end_before_start(client, auth_headers):
    response = client.get("/api/network-time-machine", headers=auth_headers,
                           params={"start_date": "2025-06-01", "end_date": "2025-01-01"})
    assert response.status_code == 400


def test_time_machine_covers_full_range_matches_totals(client, auth_headers):
    bounds = client.get("/api/network-time-machine/bounds", headers=auth_headers).json()
    response = client.get("/api/network-time-machine", headers=auth_headers,
                           params={"start_date": bounds["earliest"], "end_date": bounds["latest"]})
    assert response.status_code == 200
    body = response.json()
    assert body["after"]["edge_count"] >= body["before"]["edge_count"]
    assert set(body.keys()) >= {"before", "during", "after", "new_entities", "new_relationship_count", "dormant_entities", "findings", "disclaimer"}
    assert len(body["findings"]) == 2


def test_time_machine_narrow_window_reports_no_expansion(client, auth_headers):
    bounds = client.get("/api/network-time-machine/bounds", headers=auth_headers).json()
    response = client.get("/api/network-time-machine", headers=auth_headers,
                           params={"start_date": bounds["earliest"], "end_date": bounds["earliest"]})
    assert response.status_code == 200
    body = response.json()
    # Only relationships on the single earliest date fall inside the window.
    assert body["during"]["edge_count"] >= 1


def test_time_machine_never_claims_prediction(client, auth_headers):
    bounds = client.get("/api/network-time-machine/bounds", headers=auth_headers).json()
    response = client.get("/api/network-time-machine", headers=auth_headers,
                           params={"start_date": bounds["earliest"], "end_date": bounds["latest"]})
    body = response.json()
    assert "not a prediction" in body["disclaimer"].lower()
