from __future__ import annotations


def test_exam_overview_requires_auth(client):
    resp = client.get("/exam/overview", params={"subject": "Data Structures"})
    assert resp.status_code == 401


def test_exam_overview_returns_seeded_priority_data(client, auth_headers, seeded_subject):
    resp = client.get("/exam/overview", params={"subject": "Data Structures"}, headers=auth_headers)
    assert resp.status_code == 200
    modules = resp.json()
    assert len(modules) >= 1
    module_one = next(m for m in modules if m["module_no"] == 1)
    assert "Topic 1.1" in module_one["high_priority_topics"]


def test_exam_pyq_queue_includes_seeded_question(client, auth_headers, seeded_subject):
    resp = client.get("/exam/pyq-queue", params={"subject": "Data Structures"}, headers=auth_headers)
    assert resp.status_code == 200
    questions = [item["question_text"] for item in resp.json()]
    assert "Explain the topic." in questions


def test_teach_topic_returns_valid_lesson(client, auth_headers, seeded_subject, mock_openai):
    resp = client.post(
        "/exam/teach-topic",
        json={"subject": "Data Structures", "topic": seeded_subject["topic_name"]},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["simple_explanation"]
    assert isinstance(body["key_points"], list)


def test_answer_question_returns_answer(client, auth_headers, seeded_subject, mock_openai):
    resp = client.post(
        "/exam/answer-question",
        json={"subject": "Data Structures", "question_text": "Explain the topic.", "topic": seeded_subject["topic_name"]},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["answer"]


def test_answer_question_with_unmatched_topic_still_returns_real_answer(
    client, auth_headers, seeded_subject, mock_openai
):
    """Regression test: a `topic` that doesn't exactly match a row in the
    topics table (e.g. a PYQ's free-text topic label that differs from its
    fuzzy-linked topic's canonical name) used to make the internal progress-
    tracking lookup raise, which silently fell through to generic filler
    text instead of the real AI answer — found by api/evals against the
    live OpenAI API, since the filler text passed every mocked check here
    by trivially echoing the question back."""
    resp = client.post(
        "/exam/answer-question",
        json={
            "subject": "Data Structures",
            "question_text": "Explain the topic.",
            "topic": "A Topic Name That Does Not Exist In The Topics Table",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["answer"] == "This is a mocked AI response for testing."


def test_chat_ask_returns_mocked_reply(client, auth_headers, seeded_subject, mock_openai):
    resp = client.post(
        "/chat/ask",
        json={"subject": "Data Structures", "question": "What is this topic about?"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["reply"]


def test_chat_history_starts_empty_then_grows_after_ask(client, auth_headers, seeded_subject, mock_openai):
    empty_resp = client.get("/chat/history", params={"subject": "Data Structures"}, headers=auth_headers)
    assert empty_resp.status_code == 200
    assert empty_resp.json() == []

    client.post(
        "/chat/ask",
        json={"subject": "Data Structures", "question": "A question for history."},
        headers=auth_headers,
    )

    history_resp = client.get("/chat/history", params={"subject": "Data Structures"}, headers=auth_headers)
    roles = [m["role"] for m in history_resp.json()]
    assert "user" in roles
    assert "assistant" in roles


def test_chat_ask_rate_limit_trips_after_fifteen_calls(client, auth_headers, seeded_subject, mock_openai):
    statuses = []
    for _ in range(17):
        resp = client.post(
            "/chat/ask",
            json={"subject": "Data Structures", "question": "spam"},
            headers=auth_headers,
        )
        statuses.append(resp.status_code)

    assert 429 in statuses
