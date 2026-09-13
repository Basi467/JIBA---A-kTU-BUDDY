from __future__ import annotations

from datetime import date, timedelta


def _future_date(days: int = 7) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


def test_generate_requires_auth(client):
    resp = client.post(
        "/study-plan/generate",
        json={"subject": "Data Structures", "exam_date": _future_date(), "hours_per_day": 3},
    )
    assert resp.status_code == 401


def test_generate_returns_plan_for_seeded_subject(client, auth_headers, seeded_subject):
    resp = client.post(
        "/study-plan/generate",
        json={"subject": "Data Structures", "exam_date": _future_date(), "hours_per_day": 3},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text

    plan = resp.json()
    assert len(plan) == 1
    item = plan[0]
    assert item["subject_name"] == "Data Structures"
    assert item["topic_name"] == seeded_subject["topic_name"]
    assert item["priority_label"] == "High"
    assert item["recommended_hours"] > 0


def test_generate_weighs_manual_weak_topics_higher(client, auth_headers, seeded_subject):
    resp = client.post(
        "/study-plan/generate",
        json={
            "subject": "Data Structures",
            "exam_date": _future_date(),
            "hours_per_day": 3,
            "manual_weak_topics": [seeded_subject["topic_name"]],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()[0]["priority_score"] > 0


def test_generate_rejects_subject_with_no_priority_data(client, auth_headers, seeded_subject):
    resp = client.post(
        "/study-plan/generate",
        json={
            "subject": "A Subject That Does Not Exist",
            "exam_date": _future_date(),
            "hours_per_day": 3,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "No module-topic priority data" in resp.json()["detail"]


def test_generate_rejects_past_exam_date(client, auth_headers, seeded_subject):
    resp = client.post(
        "/study-plan/generate",
        json={
            "subject": "Data Structures",
            "exam_date": _future_date(-1),
            "hours_per_day": 3,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "future" in resp.json()["detail"].lower()


def test_generate_rejects_zero_hours_per_day(client, auth_headers, seeded_subject):
    resp = client.post(
        "/study-plan/generate",
        json={"subject": "Data Structures", "exam_date": _future_date(), "hours_per_day": 0},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "Hours per day" in resp.json()["detail"]
