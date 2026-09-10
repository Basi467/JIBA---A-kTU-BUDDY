from __future__ import annotations


def test_list_subjects_requires_auth(client):
    resp = client.get("/subjects")
    assert resp.status_code == 401


def test_list_subjects_returns_only_complete_subjects_for_users_own_scope(
    client, auth_headers, seeded_subject
):
    resp = client.get("/subjects", headers=auth_headers)
    assert resp.status_code == 200

    subjects = resp.json()
    codes = [s["subject_code"] for s in subjects]
    assert "CST205" in codes


def test_list_subjects_empty_for_scope_with_no_seeded_data(client):
    register_payload = {
        "name": "No Subjects User",
        "email": "no.subjects@example.com",
        "password": "nosubjects123",
        "scheme": "KTU_2015",  # deliberately a scheme seeded_subject never uses
        "department": "ME",
        "semester": 7,
    }
    client.post("/auth/register", json=register_payload)
    login_resp = client.post(
        "/auth/login",
        json={"email": register_payload["email"], "password": register_payload["password"]},
    )
    token = login_resp.json()["token"]

    resp = client.get("/subjects", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json() == []
