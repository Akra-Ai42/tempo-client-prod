"""Test santé de l'API — s'assure que l'app démarre."""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
