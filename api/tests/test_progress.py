from __future__ import annotations


def test_get_progress_requires_auth(client):
    resp = client.get("/progress", params={"subject": "Data Structures"})
    assert resp.status_code == 401


def test_get_progress_empty_before_any_activity(client, auth_headers, seeded_subject):
    resp = client.get("/progress", params={"subject": "Data Structures"}, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["weak"] == []
    assert body["completed"] == []
    assert body["in_progress"] == []
    assert body["progress_ratio"] == 0.0


def test_mark_progress_completed_then_reflected_in_get(client, auth_headers, seeded_subject):
    topic_name = seeded_subject["topic_name"]

    mark_resp = client.post(
        "/progress/mark",
        json={"subject": "Data Structures", "topic": topic_name, "action": "completed"},
        headers=auth_headers,
    )
    assert mark_resp.status_code == 200, mark_resp.text

    progress_resp = client.get("/progress", params={"subject": "Data Structures"}, headers=auth_headers)
    body = progress_resp.json()
    assert topic_name in body["completed"]
    assert body["progress_ratio"] == 1.0


def test_mark_progress_invalid_action_rejected(client, auth_headers, seeded_subject):
    resp = client.post(
        "/progress/mark",
        json={"subject": "Data Structures", "topic": seeded_subject["topic_name"], "action": "not_a_real_action"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_mark_progress_unknown_topic_returns_404(client, auth_headers, seeded_subject):
    resp = client.post(
        "/progress/mark",
        json={"subject": "Data Structures", "topic": "Topic That Does Not Exist", "action": "weak"},
        headers=auth_headers,
    )
    assert resp.status_code == 404
