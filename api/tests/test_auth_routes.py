from __future__ import annotations


def test_register_login_me_happy_path(client):
    register_payload = {
        "name": "Route Test User",
        "email": "route.test@example.com",
        "password": "routepass123",
        "scheme": "KTU_2019",
        "department": "CSE",
        "semester": 3,
    }
    register_resp = client.post("/auth/register", json=register_payload)
    assert register_resp.status_code == 201, register_resp.text
    assert "user_id" in register_resp.json()

    login_resp = client.post(
        "/auth/login",
        json={"email": register_payload["email"], "password": register_payload["password"]},
    )
    assert login_resp.status_code == 200, login_resp.text
    body = login_resp.json()
    assert body["user"]["email"] == register_payload["email"]
    token = body["token"]

    me_resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == register_payload["email"]


def test_login_wrong_password_returns_401(client):
    client.post(
        "/auth/register",
        json={
            "name": "Wrong Pass User",
            "email": "wrongpass.test@example.com",
            "password": "correctpass",
            "scheme": "KTU_2019",
            "department": "CSE",
            "semester": 3,
        },
    )

    resp = client.post(
        "/auth/login",
        json={"email": "wrongpass.test@example.com", "password": "incorrectpass"},
    )
    assert resp.status_code == 401


def test_register_duplicate_email_returns_409(client):
    payload = {
        "name": "Dup Route User",
        "email": "dup.route@example.com",
        "password": "duppass123",
        "scheme": "KTU_2019",
        "department": "CSE",
        "semester": 3,
    }
    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/auth/register", json=payload)
    assert second.status_code == 409


def test_me_without_token_returns_401(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_with_garbage_token_returns_401(client):
    resp = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


def test_login_rate_limit_trips_after_eight_attempts(client):
    payload = {"email": "rate.limit.test@example.com", "password": "wrongpass"}

    statuses = [client.post("/auth/login", json=payload).status_code for _ in range(10)]

    assert statuses[:8] == [401] * 8
    assert 429 in statuses[8:]
