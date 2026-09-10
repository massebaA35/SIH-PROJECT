def test_login_success(client):
    response = client.post("/api/auth/login", json={"username": "investigator.demo", "password": "InvestigatorDemo@123"})
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["user"]["role"] == "INVESTIGATOR"


def test_login_wrong_password(client):
    response = client.post("/api/auth/login", json={"username": "investigator.demo", "password": "wrong-password"})
    assert response.status_code == 401


def test_login_unknown_user(client):
    response = client.post("/api/auth/login", json={"username": "nobody", "password": "x"})
    assert response.status_code == 401


def test_me_requires_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user(client, auth_headers):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "investigator.demo"


def test_rbac_analyst_cannot_patch_alerts(client, analyst_token):
    response = client.patch(
        "/api/alerts/ALERT-0001",
        json={"status": "VERIFIED"},
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert response.status_code == 403


def test_rbac_investigator_can_patch_alerts(client, auth_headers):
    alerts = client.get("/api/alerts", headers=auth_headers).json()["items"]
    assert alerts, "expected the seeded dataset to produce at least one alert"
    alert_id = alerts[0]["id"]
    response = client.patch(f"/api/alerts/{alert_id}", json={"status": "UNDER_REVIEW"}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "UNDER_REVIEW"


def test_password_is_hashed_not_plaintext():
    from app.security.auth import hash_password, verify_password
    hashed = hash_password("Sup3rSecret!")
    assert hashed != "Sup3rSecret!"
    assert verify_password("Sup3rSecret!", hashed)
    assert not verify_password("wrong", hashed)
