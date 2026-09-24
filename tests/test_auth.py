from dataclasses import replace

import pytest

from config import _validate, get_settings
from tests.conftest import API_KEY_HEADERS


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/resume/upload"),
        ("post", "/resume/parse/some-id"),
        ("get", "/search/?q=python"),
        ("post", "/outreach/"),
        ("get", "/profile/"),
        ("put", "/profile/"),
        ("post", "/background/run/some-id"),
    ],
)
def test_protected_routes_require_auth(client, method, path):
    response = getattr(client, method)(path)

    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid credentials"}


def test_invalid_api_key_rejected(client):
    response = client.get("/search/?q=python", headers={"X-API-Key": "wrong"})

    assert response.status_code == 401


def test_valid_api_key_reaches_handler(client, monkeypatch):
    monkeypatch.setattr("routes.search.semantic_search", lambda q, top_k=5: [])

    response = client.get("/search/?q=python", headers=API_KEY_HEADERS)

    assert response.status_code == 200
    assert response.json() == []


def test_bearer_ignored_in_api_key_mode(client, fake_db):
    fake_db.auth.add_user("good-token", "user-1", "u@example.com")

    response = client.get("/profile/", headers={"Authorization": "Bearer good-token"})

    assert response.status_code == 401


@pytest.mark.parametrize("header", ["Bearer bad-token", "Bearer ", "Basic abc", "good-token"])
def test_invalid_bearer_rejected(client, fake_db, override_settings, header):
    override_settings(auth_mode="bearer")
    fake_db.auth.add_user("good-token", "user-1", "u@example.com")

    response = client.get("/profile/", headers={"Authorization": header})

    assert response.status_code == 401


def test_valid_bearer_reaches_handler_as_that_user(client, fake_db, override_settings):
    override_settings(auth_mode="bearer")
    fake_db.auth.add_user("good-token", "user-1", "u@example.com")

    response = client.get("/profile/", headers={"Authorization": "Bearer good-token"})

    assert response.status_code == 200
    assert response.json()["id"] == "user-1"
    assert response.json()["email"] == "u@example.com"


def test_api_key_or_bearer_accepts_either(client, fake_db, override_settings, monkeypatch):
    override_settings(auth_mode="api_key_or_bearer")
    fake_db.auth.add_user("good-token", "user-1", "u@example.com")
    monkeypatch.setattr("routes.search.semantic_search", lambda q, top_k=5: [])

    assert client.get("/search/?q=x", headers=API_KEY_HEADERS).status_code == 200
    assert client.get("/search/?q=x", headers={"Authorization": "Bearer good-token"}).status_code == 200
    assert client.get("/search/?q=x", headers={"X-API-Key": "nope"}).status_code == 401


def test_auth_off_allows_anonymous(client, override_settings, monkeypatch):
    override_settings(auth_mode="off")
    monkeypatch.setattr("routes.search.semantic_search", lambda q, top_k=5: [])

    assert client.get("/search/?q=x").status_code == 200


@pytest.mark.parametrize(
    "changes",
    [
        {"auth_mode": "nonsense"},
        {"auth_mode": "api_key", "api_key": None},
        {"app_env": "production", "auth_mode": "off"},
        {"app_env": "production", "cors_allow_origins": ["*"]},
    ],
)
def test_unsafe_settings_rejected(changes):
    with pytest.raises(RuntimeError):
        _validate(replace(get_settings(), **changes))
