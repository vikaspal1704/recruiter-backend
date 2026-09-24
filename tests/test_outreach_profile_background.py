import routes.outreach
from tests.conftest import API_KEY_HEADERS, add_candidate

PAYLOAD = {"candidate_id": "cand-1", "subject": "Hello", "body": "<p>Hi Jane</p>"}


def test_outreach_candidate_missing_is_404(client, monkeypatch):
    monkeypatch.setattr(routes.outreach, "send_email", lambda *a: (202, ""))

    response = client.post("/outreach/", json=PAYLOAD, headers=API_KEY_HEADERS)

    assert response.status_code == 404


def test_outreach_sends_and_logs(client, fake_db, monkeypatch):
    add_candidate(fake_db)
    sent = []
    monkeypatch.setattr(
        routes.outreach, "send_email", lambda to, subject, body: sent.append(to) or (202, "")
    )

    response = client.post("/outreach/", json=PAYLOAD, headers=API_KEY_HEADERS)

    assert response.status_code == 200
    assert response.json() == {"status": "sent", "to": "jane.doe@example.com"}
    assert sent == ["jane.doe@example.com"]
    [log] = fake_db.tables["outreach_logs"]
    assert log["candidate_id"] == "cand-1"
    assert log["sent_by"] == "00000000-0000-0000-0000-000000000000"
    assert log["channel"] == "email"


def test_outreach_sendgrid_failure_is_500(client, fake_db, monkeypatch):
    add_candidate(fake_db)
    monkeypatch.setattr(routes.outreach, "send_email", lambda *a: (400, "bad request"))

    response = client.post("/outreach/", json=PAYLOAD, headers=API_KEY_HEADERS)

    assert response.status_code == 500
    assert "outreach_logs" not in fake_db.tables


def test_outreach_sendgrid_exception_is_500(client, fake_db, monkeypatch):
    add_candidate(fake_db)

    def boom(*_args):
        raise RuntimeError("network down")

    monkeypatch.setattr(routes.outreach, "send_email", boom)

    response = client.post("/outreach/", json=PAYLOAD, headers=API_KEY_HEADERS)

    assert response.status_code == 500
    assert response.json() == {"detail": "Email send failed"}


def test_profile_get_creates_blank_when_missing(client, fake_db):
    response = client.get("/profile/", headers=API_KEY_HEADERS)

    assert response.status_code == 200
    assert response.json()["id"] == "00000000-0000-0000-0000-000000000000"
    assert len(fake_db.tables["profiles"]) == 1

    # Second call returns the same row instead of inserting again.
    assert client.get("/profile/", headers=API_KEY_HEADERS).status_code == 200
    assert len(fake_db.tables["profiles"]) == 1


def test_profile_put_empty_body_is_400(client):
    response = client.put("/profile/", json={}, headers=API_KEY_HEADERS)

    assert response.status_code == 400


def test_profile_put_updates_fields(client, fake_db):
    client.get("/profile/", headers=API_KEY_HEADERS)

    response = client.put(
        "/profile/", json={"full_name": "Vikas Pal", "location": "Remote"}, headers=API_KEY_HEADERS
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Vikas Pal"
    assert response.json()["location"] == "Remote"
    assert "current_title" not in response.json()


def test_profile_put_without_row_is_404(client):
    response = client.put("/profile/", json={"full_name": "X"}, headers=API_KEY_HEADERS)

    assert response.status_code == 404


def test_background_stub_returns_passed(client, fake_db):
    add_candidate(fake_db)

    response = client.post("/background/run/cand-1", headers=API_KEY_HEADERS)

    assert response.status_code == 200
    assert response.json() == {
        "status": "passed",
        "report_url": "https://example.com/fake-report.pdf",
    }
    [check] = fake_db.tables["background_checks"]
    assert check["status"] == "passed"


def test_background_unknown_candidate_is_404(client):
    response = client.post("/background/run/nope", headers=API_KEY_HEADERS)

    assert response.status_code == 404
