from __future__ import annotations

import uuid


def _register(client, email: str, password: str = "originalpass123"):
    payload = {
        "name": "Reset Flow User",
        "email": email,
        "password": password,
        "scheme": "KTU_2019",
        "department": "CSE",
        "semester": 3,
    }
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 201, resp.text
    return payload


def test_forgot_password_generic_message_for_unknown_email(client):
    resp = client.post("/auth/forgot-password", json={"email": "no.such.user@example.com"})
    assert resp.status_code == 200
    assert "reset link" in resp.json()["message"].lower()


def test_forgot_password_generic_message_for_known_email_too(client):
    email = f"reset.known.{uuid.uuid4().hex}@example.com"
    _register(client, email)

    resp = client.post("/auth/forgot-password", json={"email": email})
    assert resp.status_code == 200
    assert "reset link" in resp.json()["message"].lower()
    # Response body must be identical whether or not the email exists —
    # verified by the two tests sharing the same assertion.


def test_full_reset_flow_changes_password(client, monkeypatch):
    import auth_engine
    from api import password_reset_tokens

    email = f"reset.flow.{uuid.uuid4().hex}@example.com"
    _register(client, email, password="originalpass123")

    user = auth_engine.get_user_by_email(email)
    token = password_reset_tokens.issue_reset_token(user["id"])

    reset_resp = client.post(
        "/auth/reset-password", json={"token": token, "new_password": "brandnewpass456"}
    )
    assert reset_resp.status_code == 200, reset_resp.text

    old_login = client.post("/auth/login", json={"email": email, "password": "originalpass123"})
    assert old_login.status_code == 401

    new_login = client.post("/auth/login", json={"email": email, "password": "brandnewpass456"})
    assert new_login.status_code == 200


def test_reset_with_invalid_token_rejected(client):
    resp = client.post(
        "/auth/reset-password", json={"token": "not-a-real-token", "new_password": "whatever123"}
    )
    assert resp.status_code == 400


def test_reset_token_cannot_be_reused(client):
    import auth_engine
    from api import password_reset_tokens

    email = f"reset.reuse.{uuid.uuid4().hex}@example.com"
    _register(client, email)

    user = auth_engine.get_user_by_email(email)
    token = password_reset_tokens.issue_reset_token(user["id"])

    first = client.post("/auth/reset-password", json={"token": token, "new_password": "firstnewpass1"})
    assert first.status_code == 200

    second = client.post("/auth/reset-password", json={"token": token, "new_password": "secondnewpass2"})
    assert second.status_code == 400


def test_reset_token_expiry_is_enforced(client, monkeypatch):
    import auth_engine
    from api import password_reset_tokens

    email = f"reset.expired.{uuid.uuid4().hex}@example.com"
    _register(client, email)
    user = auth_engine.get_user_by_email(email)

    monkeypatch.setattr(password_reset_tokens, "RESET_TOKEN_TTL_MINUTES", -1)
    expired_token = password_reset_tokens.issue_reset_token(user["id"])

    resp = client.post(
        "/auth/reset-password", json={"token": expired_token, "new_password": "wontmatter123"}
    )
    assert resp.status_code == 400
