from __future__ import annotations


def test_signup_options_does_not_require_auth(client):
    resp = client.get("/meta/signup-options")
    assert resp.status_code == 200


def test_signup_options_includes_seeded_subject_scope(client, seeded_subject):
    resp = client.get("/meta/signup-options")
    assert resp.status_code == 200

    body = resp.json()
    scheme_entry = next((s for s in body if s["scheme"] == "KTU_2019"), None)
    assert scheme_entry is not None, f"KTU_2019 not in {body}"

    dept_entry = next((d for d in scheme_entry["departments"] if d["department"] == "CSE"), None)
    assert dept_entry is not None, f"CSE not in {scheme_entry['departments']}"
    assert 3 in dept_entry["semesters"]


def test_signup_options_shape_matches_schema(client, seeded_subject):
    resp = client.get("/meta/signup-options")
    body = resp.json()

    assert isinstance(body, list)
    for scheme_entry in body:
        assert "scheme" in scheme_entry
        assert "departments" in scheme_entry
        for dept_entry in scheme_entry["departments"]:
            assert "department" in dept_entry
            assert isinstance(dept_entry["semesters"], list)
            assert all(isinstance(s, int) for s in dept_entry["semesters"])
