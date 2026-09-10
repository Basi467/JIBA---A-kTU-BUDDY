from __future__ import annotations

import pytest


def test_hash_password_roundtrip(db_path):
    import auth_engine

    hashed = auth_engine.hash_password("correct horse battery staple")
    assert hashed.startswith("pbkdf2$")
    assert auth_engine.verify_password("correct horse battery staple", hashed)
    assert not auth_engine.verify_password("wrong password", hashed)


def test_hash_password_uses_random_salt(db_path):
    import auth_engine

    first = auth_engine.hash_password("same-password")
    second = auth_engine.hash_password("same-password")
    assert first != second, "two hashes of the same password must not collide"


def test_verify_password_legacy_sha256_format(db_path):
    import hashlib

    import auth_engine

    salt = "somesalt"
    legacy_hash = f"{salt}${hashlib.sha256((salt + 'legacy-pass').encode()).hexdigest()}"
    assert auth_engine.verify_password("legacy-pass", legacy_hash)
    assert not auth_engine.verify_password("wrong-pass", legacy_hash)


def test_verify_password_rejects_garbage_hash(db_path):
    import auth_engine

    assert not auth_engine.verify_password("anything", "not-a-real-hash-format")


def test_register_and_login_user(db_path):
    import auth_engine

    user_id = auth_engine.register_user(
        name="Engine Test User",
        email="engine.test@example.com",
        password="enginepass",
        scheme="KTU_2019",
        department="CSE",
        semester=3,
    )
    assert isinstance(user_id, int)

    user = auth_engine.login_user("engine.test@example.com", "enginepass")
    assert user is not None
    assert user["email"] == "engine.test@example.com"

    assert auth_engine.login_user("engine.test@example.com", "wrongpass") is None


def test_register_duplicate_email_rejected(db_path):
    import auth_engine

    auth_engine.register_user(
        name="Dup User",
        email="dup.test@example.com",
        password="pass12345",
        scheme="KTU_2019",
        department="CSE",
        semester=3,
    )
    with pytest.raises(ValueError):
        auth_engine.register_user(
            name="Dup User Again",
            email="DUP.TEST@example.com",  # case-insensitive collision
            password="pass12345",
            scheme="KTU_2019",
            department="CSE",
            semester=3,
        )
