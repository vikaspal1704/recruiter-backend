import os

# Must be set before the app (and its settings) are imported.
TEST_ENV = {
    "APP_ENV": "test",
    "AUTH_MODE": "api_key",
    "API_KEY": "test-api-key",
    "SUPABASE_URL": "https://example.supabase.co",
    "SUPABASE_SERVICE_KEY": "test-service-key",
    "OPENAI_API_KEY": "test-openai",
    "PINECONE_API_KEY": "test-pinecone",
    "PINECONE_ENVIRONMENT": "us-east-1",
    "PINECONE_INDEX_NAME": "candidates-mvp",
    "SENDGRID_API_KEY": "test-sendgrid",
    "SENDGRID_FROM_EMAIL": "noreply@example.com",
    "CORS_ALLOW_ORIGINS": "http://localhost:3000",
}
os.environ.update(TEST_ENV)

from dataclasses import replace  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import dependencies  # noqa: E402
import routes.background  # noqa: E402
import routes.outreach  # noqa: E402
import routes.profile  # noqa: E402
import routes.resume  # noqa: E402
import routes.search  # noqa: E402
from app import app  # noqa: E402
from config import get_settings  # noqa: E402
from tests.fakes import FakeIndex, FakeSupabase  # noqa: E402

API_KEY_HEADERS = {"X-API-Key": "test-api-key"}
SAMPLE_PDF = Path(__file__).parent / "fixtures" / "sample_resume.pdf"

_SUPABASE_USERS = (
    dependencies,
    routes.resume,
    routes.search,
    routes.outreach,
    routes.profile,
    routes.background,
)


@pytest.fixture
def fake_db(monkeypatch) -> FakeSupabase:
    fake = FakeSupabase()
    for module in _SUPABASE_USERS:
        monkeypatch.setattr(module, "supabase", fake)
    return fake


@pytest.fixture
def fake_index(monkeypatch) -> FakeIndex:
    fake = FakeIndex()
    monkeypatch.setattr(routes.resume, "index", fake)
    return fake


@pytest.fixture
def client(fake_db, fake_index) -> TestClient:
    return TestClient(app)


@pytest.fixture
def override_settings():
    """Override settings for one test, e.g. override_settings(auth_mode="bearer")."""

    def apply(**changes):
        settings = replace(get_settings(), **changes)
        app.dependency_overrides[get_settings] = lambda: settings
        return settings

    yield apply
    app.dependency_overrides.pop(get_settings, None)


@pytest.fixture
def sample_pdf() -> bytes:
    return SAMPLE_PDF.read_bytes()


def add_candidate(fake_db: FakeSupabase, **overrides) -> dict:
    row = {
        "id": "cand-1",
        "resume_id": "res-1",
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "skills": ["Python", "FastAPI"],
        "years_experience": 5.0,
        "education": "B.Tech",
        "raw_text": "Jane Doe ...",
        **overrides,
    }
    fake_db.tables.setdefault("candidate_profiles", []).append(row)
    return row
