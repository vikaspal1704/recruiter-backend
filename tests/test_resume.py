import pytest

import routes.resume
from services import resume_parser
from tests.conftest import API_KEY_HEADERS, add_candidate

PARSED = {
    "name": "Jane Doe",
    "email": "jane.doe@example.com",
    "skills": ["Python", "FastAPI"],
    "years_experience": 5,
    "education": "B.Tech Computer Science",
}


def _upload(client, content: bytes, filename: str = "cv.pdf", headers=API_KEY_HEADERS):
    return client.post(
        "/resume/upload",
        files={"file": (filename, content, "application/pdf")},
        headers=headers,
    )


def test_upload_pdf_stores_file_and_row(client, fake_db, sample_pdf):
    response = _upload(client, sample_pdf)

    assert response.status_code == 200
    resume_id = response.json()["resume_id"]
    [row] = fake_db.tables["resumes"]
    assert row["id"] == resume_id
    # API-key principal is the documented system user.
    assert row["user_id"] == "00000000-0000-0000-0000-000000000000"
    assert row["file_url"].endswith("/resumes/00000000-0000-0000-0000-000000000000/cv.pdf")
    assert fake_db.storage.files["resumes"]["00000000-0000-0000-0000-000000000000/cv.pdf"]


def test_upload_uses_bearer_user_id(client, fake_db, sample_pdf, override_settings):
    override_settings(auth_mode="bearer")
    fake_db.auth.add_user("tok", "user-42", "r@example.com")

    response = _upload(client, sample_pdf, headers={"Authorization": "Bearer tok"})

    assert response.status_code == 200
    assert fake_db.tables["resumes"][0]["user_id"] == "user-42"


def test_upload_strips_path_from_filename(client, fake_db, sample_pdf):
    _upload(client, sample_pdf, filename="../../etc/cv.pdf")

    assert list(fake_db.storage.files["resumes"]) == [
        "00000000-0000-0000-0000-000000000000/cv.pdf"
    ]


def test_upload_rejects_non_pdf(client, fake_db):
    response = _upload(client, b"hello, not a pdf", filename="cv.txt")

    assert response.status_code == 400
    assert "resumes" not in fake_db.tables


def test_upload_rejects_too_large(client, override_settings, sample_pdf):
    override_settings(max_upload_bytes=100)

    response = _upload(client, sample_pdf)

    assert response.status_code == 413


def test_upload_without_file_is_422(client):
    response = client.post("/resume/upload", data={"not": "a file"}, headers=API_KEY_HEADERS)

    assert response.status_code == 422


def test_parse_unknown_resume_is_404(client):
    response = client.post("/resume/parse/does-not-exist", headers=API_KEY_HEADERS)

    assert response.status_code == 404
    assert response.json() == {"detail": "Resume not found"}


def test_parse_already_parsed_returns_existing_without_reembedding(
    client, fake_db, fake_index, monkeypatch
):
    fake_db.tables["resumes"] = [{"id": "res-1", "file_url": "u", "parsed": True}]
    existing = add_candidate(fake_db)

    def fail(*_args):
        raise AssertionError("must not re-parse or re-embed")

    monkeypatch.setattr(routes.resume, "extract_text_from_pdf", fail)
    monkeypatch.setattr(routes.resume, "embed_text", fail)

    response = client.post("/resume/parse/res-1", headers=API_KEY_HEADERS)

    assert response.status_code == 200
    assert response.json() == existing
    assert fake_index.vectors == {}


def test_parse_fresh_resume(client, fake_db, fake_index, monkeypatch):
    fake_db.tables["resumes"] = [{"id": "res-1", "file_url": "https://f/cv.pdf", "parsed": False}]
    monkeypatch.setattr(routes.resume, "extract_text_from_pdf", lambda url: "raw resume text")
    monkeypatch.setattr(routes.resume, "parse_resume_text", lambda text: dict(PARSED))
    monkeypatch.setattr(routes.resume, "embed_text", lambda text: [0.1, 0.2])

    response = client.post("/resume/parse/res-1", headers=API_KEY_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["resume_id"] == "res-1"
    assert body["name"] == "Jane Doe"
    assert body["skills"] == ["Python", "FastAPI"]
    assert body["years_experience"] == 5.0
    assert body["raw_text"] == "raw resume text"
    assert fake_index.vectors[body["id"]] == ([0.1, 0.2], {"candidate_profile_id": body["id"]})
    assert fake_db.tables["resumes"][0]["parsed"] is True


def test_parse_failure_is_500_and_leaves_resume_unparsed(client, fake_db, monkeypatch):
    fake_db.tables["resumes"] = [{"id": "res-1", "file_url": "u", "parsed": False}]
    monkeypatch.setattr(routes.resume, "extract_text_from_pdf", lambda url: "text")
    monkeypatch.setattr(routes.resume, "parse_resume_text", lambda text: dict(PARSED))

    def embed_down(_text):
        raise RuntimeError("openai down")

    monkeypatch.setattr(routes.resume, "embed_text", embed_down)

    response = client.post("/resume/parse/res-1", headers=API_KEY_HEADERS)

    assert response.status_code == 500
    assert "openai down" in response.json()["detail"]
    assert fake_db.tables["resumes"][0]["parsed"] is False
    assert "candidate_profiles" not in fake_db.tables


def test_extract_text_from_pdf_reads_downloaded_bytes(monkeypatch, sample_pdf):
    class Resp:
        content = sample_pdf

        def raise_for_status(self):
            pass

    monkeypatch.setattr(resume_parser.requests, "get", lambda url, timeout: Resp())

    text = resume_parser.extract_text_from_pdf("https://example.com/cv.pdf")

    assert "Jane Doe" in text
    assert "FastAPI" in text


def test_parse_resume_text_uses_openai_json(monkeypatch):
    class Completions:
        @staticmethod
        def create(**kwargs):
            assert kwargs["temperature"] == 0
            message = type("M", (), {"content": '{"name": "Jane"}'})
            return type("R", (), {"choices": [type("C", (), {"message": message})]})

    fake_openai = type("O", (), {"chat": type("Chat", (), {"completions": Completions})})
    monkeypatch.setattr(resume_parser, "openai", fake_openai)

    assert resume_parser.parse_resume_text("text") == {"name": "Jane"}


def test_parse_resume_text_rejects_non_json(monkeypatch):
    message = type("M", (), {"content": "not json"})
    response = type("R", (), {"choices": [type("C", (), {"message": message})]})
    completions = type("Cp", (), {"create": staticmethod(lambda **_: response)})
    monkeypatch.setattr(
        resume_parser, "openai", type("O", (), {"chat": type("Ch", (), {"completions": completions})})
    )

    with pytest.raises(RuntimeError, match="Failed to parse JSON"):
        resume_parser.parse_resume_text("text")
