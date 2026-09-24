def test_healthcheck_is_public(client):
    response = client.get("/healthcheck")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["version"]


def test_openapi_lists_expected_tags(client):
    spec = client.get("/openapi.json").json()

    assert spec["info"]["title"] == "Recruiter Talent Search API"
    tags = {tag for path in spec["paths"].values() for op in path.values() for tag in op["tags"]}
    assert {"health", "resume", "search", "outreach", "profile", "background"} <= tags


def test_cors_allows_configured_origin_only(client):
    allowed = client.options(
        "/healthcheck",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
    )
    denied = client.options(
        "/healthcheck",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )

    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert "access-control-allow-origin" not in denied.headers
