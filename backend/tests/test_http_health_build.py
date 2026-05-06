"""HTTP smoke: /health exposes build id (confirms which app instance is running)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def test_health_includes_app_build_id():
    app = create_app()
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"
    assert "app_build_id" in data
    assert "env" in data
    assert "git_commit" in data
    assert "analyzer_graph_revision" in data


def test_push_token_endpoint_requires_auth():
    app = create_app()
    client = TestClient(app)
    r = client.post("/family/push-tokens", json={"provider": "fcm", "platform": "android", "token": "x" * 64})
    assert r.status_code in (401, 403)


def test_version_matches_health_core_fields():
    app = create_app()
    client = TestClient(app)
    h = client.get("/health").json()
    v = client.get("/version").json()
    assert v["app_build_id"] == h["app_build_id"]
    assert v["analyzer_graph_revision"] == h["analyzer_graph_revision"]
    assert v["git_commit"] == h["git_commit"]
