import routes.search
from tests.conftest import API_KEY_HEADERS, add_candidate


def test_search_requires_q(client):
    response = client.get("/search/", headers=API_KEY_HEADERS)

    assert response.status_code == 422


def test_search_rejects_non_positive_k(client):
    response = client.get("/search/?q=python&k=0", headers=API_KEY_HEADERS)

    assert response.status_code == 422


def test_search_returns_hydrated_results(client, fake_db, monkeypatch):
    add_candidate(fake_db, id="cand-1", name="Jane Doe")
    add_candidate(fake_db, id="cand-2", name="John Roe", skills=["Go"])
    calls = []

    def fake_search(q, top_k=5):
        calls.append((q, top_k))
        return [
            {"metadata": {"candidate_profile_id": "cand-2"}, "score": 0.91},
            {"metadata": {"candidate_profile_id": "missing"}, "score": 0.8},
            {"metadata": {"candidate_profile_id": "cand-1"}, "score": 0.75},
        ]

    monkeypatch.setattr(routes.search, "semantic_search", fake_search)

    response = client.get("/search/?q=python%20fastapi&k=3", headers=API_KEY_HEADERS)

    assert response.status_code == 200
    assert calls == [("python fastapi", 3)]
    body = response.json()
    assert [r["candidate_id"] for r in body] == ["cand-2", "cand-1"]
    assert body[0] == {
        "candidate_id": "cand-2",
        "name": "John Roe",
        "email": "jane.doe@example.com",
        "skills": ["Go"],
        "years_experience": 5.0,
        "education": "B.Tech",
        "score": 0.91,
    }


def test_search_pinecone_error_is_500(client, monkeypatch):
    def boom(q, top_k=5):
        raise RuntimeError("index unavailable")

    monkeypatch.setattr(routes.search, "semantic_search", boom)

    response = client.get("/search/?q=python", headers=API_KEY_HEADERS)

    assert response.status_code == 500
    assert response.json() == {"detail": "Pinecone error: index unavailable"}
