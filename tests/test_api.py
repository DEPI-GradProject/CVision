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
