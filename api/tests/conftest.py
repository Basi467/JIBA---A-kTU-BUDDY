from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterator

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SRC_DIR = ROOT_DIR / "src"
DATABASE_DIR = ROOT_DIR / "database"

# api/__init__.py normally does this SRC_DIR insert once uvicorn imports the
# api package; database/db.py, seed.py etc. rely on being run with their own
# directory on sys.path[0]. Neither happens automatically under pytest, so
# both are added explicitly here, before anything under test gets imported.
for _path in (ROOT_DIR, SRC_DIR, DATABASE_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))


@pytest.fixture(scope="session")
def db_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A fresh sqlite file for the whole test session, migrated to the
    latest schema. KTU_DB_PATH must be set before any app-side module is
    imported, since several of them resolve their DB_PATH once at import
    time (see src/db_path.py) — that's why this fixture, not a plain
    autouse env-var fixture, is the thing every other fixture here depends
    on."""
    path = tmp_path_factory.mktemp("db") / "test_ktu.db"
    os.environ["KTU_DB_PATH"] = str(path)

    from migrate import migrate  # local import: only safe after env var set

    migrate(path)
    return path


@pytest.fixture(scope="session")
def app(db_path: Path):
    from api.main import app as fastapi_app  # local import: same reason

    return fastapi_app


@pytest.fixture()
def client(app) -> Iterator["TestClient"]:  # noqa: F821 - imported below
    from fastapi.testclient import TestClient

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def _reset_rate_limits(app):
    """slowapi's in-memory storage persists counters across requests within
    the process; without this, an earlier test's calls to e.g. /auth/login
    would count toward a later test's rate-limit assertions."""
    app.state.limiter.reset()
    yield


@pytest.fixture()
def mock_openai(monkeypatch):
    """Every AI-backed feature (tutor chat, teach-topic, answer-question)
    funnels through chat_engine.get_openai_client() — patching that one spot
    covers all of them and keeps tests free, fast, and offline."""
    import chat_engine

    class _FakeMessage:
        content = "This is a mocked AI response for testing."

    class _FakeChoice:
        message = _FakeMessage()

    class _FakeCompletion:
        choices = [_FakeChoice()]

    class _FakeCompletions:
        def create(self, *args, **kwargs):
            return _FakeCompletion()

    class _FakeChat:
        completions = _FakeCompletions()

    class _FakeClient:
        chat = _FakeChat()

    monkeypatch.setattr(chat_engine, "get_openai_client", lambda: _FakeClient())
    return _FakeClient()


@pytest.fixture()
def registered_user(client) -> dict:
    """Registers and logs in a fresh user against a subject/scheme/department
    combination that matches `seeded_subject` — tests that need real subject
    data get it for free by depending on both fixtures. A random email per
    call is required because the backing db is session-scoped (one file
    shared by every test), so a fixed email would collide across tests."""
    import uuid

    payload = {
        "name": "Test Student",
        "email": f"test.student.{uuid.uuid4().hex}@example.com",
        "password": "testpass123",
        "scheme": "KTU_2019",
        "department": "CSE",
        "semester": 3,
    }
    register_resp = client.post("/auth/register", json=payload)
    assert register_resp.status_code == 201, register_resp.text

    login_resp = client.post(
        "/auth/login", json={"email": payload["email"], "password": payload["password"]}
    )
    assert login_resp.status_code == 200, login_resp.text
    body = login_resp.json()

    return {"token": body["token"], "user": body["user"], "password": payload["password"]}


@pytest.fixture()
def auth_headers(registered_user) -> dict:
    return {"Authorization": f"Bearer {registered_user['token']}"}


@pytest.fixture(scope="session")
def seeded_subject(db_path: Path) -> dict:
    """Inserts one minimal 'complete' subject (5 modules + a PYQ linked to a
    real topic) directly against db_path — the completeness bar
    auth_engine.COMPLETE_SUBJECT_FILTER enforces, matching the scheme/
    department/semester the `registered_user` fixture signs up with so the
    two compose directly in route tests."""
    import sqlite3

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO subjects (subject_code, subject_name, scheme, department, semester) "
            "VALUES (?, ?, ?, ?, ?)",
            ("CST205", "Data Structures", "KTU_2019", "CSE", 3),
        )
        subject_id = cur.lastrowid

        topic_ids = []
        for module_no in range(1, 6):
            cur.execute(
                "INSERT INTO modules (subject_id, module_no, module_title) VALUES (?, ?, ?)",
                (subject_id, module_no, f"Module {module_no}"),
            )
            module_id = cur.lastrowid
            cur.execute(
                "INSERT INTO topics (module_id, topic_name) VALUES (?, ?)",
                (module_id, f"Topic {module_no}.1"),
            )
            topic_ids.append(cur.lastrowid)

        cur.execute(
            """
            INSERT INTO pyq_questions
                (subject_id, year, exam_type, module_no, marks, question_text, topic_id, topic_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (subject_id, 2024, "regular", 1, 10, "Explain the topic.", topic_ids[0], "Topic 1.1"),
        )

        # exam_mode_engine.build_exam_mode() (and everything downstream of it —
        # teach-queue, pyq-queue) reads from module_topic_priority, not
        # pyq_questions directly, so a row here is required for those routes
        # to return anything at all.
        cur.execute(
            """
            INSERT INTO module_topic_priority
                (subject_id, module_no, topic_id, question_count, weighted_score, priority_label)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (subject_id, 1, topic_ids[0], 1, 5.0, "High"),
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "subject_id": subject_id,
        "subject_name": "Data Structures",
        "topic_name": "Topic 1.1",
        "topic_ids": topic_ids,
    }
