from __future__ import annotations


def test_predicted_requires_auth(client):
    resp = client.get("/priority/predicted", params={"subject": "Data Structures"})
    assert resp.status_code == 401


def test_predicted_returns_seeded_priority_row(client, auth_headers, seeded_subject):
    resp = client.get("/priority/predicted", params={"subject": "Data Structures"}, headers=auth_headers)
    assert resp.status_code == 200

    rows = resp.json()
    assert len(rows) == 1
    row = rows[0]
    assert row["subject_name"] == "Data Structures"
    assert row["module_no"] == 1
    assert row["topic_name"] == seeded_subject["topic_name"]
    assert row["priority_label"] == "High"
    assert row["question_count"] == 1


def test_predicted_empty_for_subject_with_no_priority_data(client, auth_headers, seeded_subject):
    resp = client.get(
        "/priority/predicted", params={"subject": "A Subject That Does Not Exist"}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json() == []
