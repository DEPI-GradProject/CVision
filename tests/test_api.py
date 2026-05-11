import os

import pytest

pytest.importorskip("sqlalchemy")
pytest.importorskip("fastapi")
pytest.importorskip("langgraph")

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from fastapi.testclient import TestClient

from api import app

client = TestClient(app)


def test_home_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] is not None


def test_latest_jobs_fails_without_db():
    response = client.get("/api/v1/jobs/latest?limit=5")
    assert response.status_code == 500


def test_training_data_fails_without_db():
    response = client.get("/api/v1/jobs/training?limit=5")
    assert response.status_code == 500


def test_analyze_cv_no_file():
    response = client.post("/api/v1/analyze-cv")
    assert response.status_code == 422


def test_analyze_cv_wrong_extension():
    response = client.post(
        "/api/v1/analyze-cv",
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_analyze_cv_stream_no_file():
    response = client.post("/api/v1/analyze-cv/stream")
    assert response.status_code == 422


def test_analyze_cv_stream_wrong_extension():
    response = client.post(
        "/api/v1/analyze-cv/stream",
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_analyze_cv_stream_too_large():
    response = client.post(
        "/api/v1/analyze-cv/stream",
        files={"file": ("test.pdf", b"x" * (11 * 1024 * 1024), "application/pdf")},
    )
    assert response.status_code == 400
    assert "too large" in response.json()["detail"].lower()


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data


def test_health_endpoint_rate_limited():
    for _ in range(35):
        client.get("/api/v1/health")
    response = client.get("/api/v1/health")
    assert response.status_code == 429
