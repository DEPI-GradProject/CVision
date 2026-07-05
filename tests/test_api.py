import asyncio
import os
from unittest.mock import Mock, patch

import pytest

pytest.importorskip("sqlalchemy")
pytest.importorskip("fastapi")
pytest.importorskip("langgraph")

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from fastapi.testclient import TestClient
from langchain_core.language_models.llms import LLM

from api import app
from auth import current_active_user
from auth.database import get_async_engine
from models.db_models import Base as DBBase

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    """Create all tables on both sync and async in-memory SQLite before tests."""
    from api import engine as _sync_engine

    DBBase.metadata.create_all(_sync_engine)

    async def _init():
        _engine = get_async_engine()
        async with _engine.begin() as _conn:
            await _conn.run_sync(DBBase.metadata.create_all)

    asyncio.run(_init())
    yield

    async def _drop():
        _engine = get_async_engine()
        async with _engine.begin() as _conn:
            await _conn.run_sync(DBBase.metadata.drop_all)

    asyncio.run(_drop())


@pytest.fixture(autouse=True)
def _auth_override():
    """Bypass real auth for tests that need it; auth-specific tests restore it."""
    yield
    app.dependency_overrides.clear()


def _auth_headers():
    """Register a user and return auth Bearer header."""
    res = client.post("/auth/register", json={"email": "test@test.com", "password": "TestPass123!"})
    if res.status_code == 422:
        # user may already exist in a previous test
        pass
    res = client.post("/auth/login", data={"username": "test@test.com", "password": "TestPass123!"})
    token = res.json().get("access_token", "")
    return {"Authorization": f"Bearer {token}"}


def _mock_user():
    user = Mock()
    user.id = 1
    user.email = "test@test.com"
    user.is_active = True
    user.is_superuser = False
    user.is_verified = True
    return user


def test_home_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] is not None


def test_latest_jobs_empty():
    response = client.get("/api/v1/jobs/latest?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"] == []


def test_training_data_empty():
    response = client.get("/api/v1/jobs/training?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"] == []


def test_auth_login_route_exists():
    response = client.post("/auth/login")
    assert response.status_code == 422


def test_auth_register_route_exists():
    response = client.post("/auth/register", json={})
    assert response.status_code == 422


def test_auth_me_requires_auth():
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_protected_analyze_cv_requires_auth():
    response = client.post("/api/v1/analyze-cv")
    assert response.status_code == 401


def _with_auth_override():
    app.dependency_overrides[current_active_user] = lambda: _mock_user()


def test_analyze_cv_no_file():
    _with_auth_override()
    response = client.post("/api/v1/analyze-cv")
    assert response.status_code == 422


def test_analyze_cv_wrong_extension():
    _with_auth_override()
    response = client.post(
        "/api/v1/analyze-cv",
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_analyze_cv_stream_no_file():
    _with_auth_override()
    response = client.post("/api/v1/analyze-cv/stream")
    assert response.status_code == 422


def test_analyze_cv_stream_wrong_extension():
    _with_auth_override()
    response = client.post(
        "/api/v1/analyze-cv/stream",
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_analyze_cv_stream_too_large():
    _with_auth_override()
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


# --- Auth integration tests ---


def test_auth_register_success():
    email = "newuser@test.com"
    password = "Str0ng!Pass"
    response = client.post("/auth/register", json={"email": email, "password": password})
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == email
    assert data["is_active"] is True


def test_auth_register_duplicate():
    response = client.post("/auth/register", json={"email": "newuser@test.com", "password": "Str0ng!Pass"})
    assert response.status_code == 400


def test_auth_login_success():
    response = client.post("/auth/login", data={"username": "newuser@test.com", "password": "Str0ng!Pass"})
    assert response.status_code == 200
    token = response.json()
    assert "access_token" in token
    assert token["token_type"] == "bearer"


def test_auth_login_wrong_password():
    response = client.post("/auth/login", data={"username": "newuser@test.com", "password": "wrongpass"})
    assert response.status_code == 400


def test_auth_me_authenticated():
    res = client.post("/auth/login", data={"username": "newuser@test.com", "password": "Str0ng!Pass"})
    token = res.json()["access_token"]
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@test.com"


# --- Protected endpoint auth checks ---


def test_history_requires_auth():
    response = client.get("/api/v1/history")
    assert response.status_code == 401


def test_history_empty():
    _with_auth_override()
    response = client.get("/api/v1/history")
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []


def test_stats_requires_auth():
    response = client.get("/api/v1/stats")
    assert response.status_code == 401


def test_stats_empty():
    _with_auth_override()
    response = client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total_analyses"] == 0


def _mock_llm_response(json_str: str):
    """Patch _get_match_llm so match-job endpoint returns controlled data."""
    mock_llm = Mock(spec=LLM)
    mock_llm.invoke.return_value = json_str
    patcher = patch("api._get_match_llm", return_value=mock_llm)
    patcher.start()
    return patcher


def test_match_job_success():
    _with_auth_override()
    patcher = _mock_llm_response(
        '{"match_score": 75, "matched_skills": ["python", "ml"],'
        ' "missing_skills": ["docker"],'
        ' "improvement_tips": ["Learn Docker", "Add cloud"],'
        ' "keyword_coverage": 0.6}'
    )
    try:
        response = client.post(
            "/api/v1/match-job",
            json={"cv_text": "Experienced Python developer", "job_description": "Looking for Python dev with ML"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["match_score"] == 75
        assert "python" in data["matched_skills"]
    finally:
        patcher.stop()


def test_match_job_requires_auth():
    response = client.post("/api/v1/match-job", json={})
    assert response.status_code == 401


def test_match_job_file_requires_auth():
    response = client.post("/api/v1/match-job/file")
    assert response.status_code == 401


def test_match_job_file_wrong_extension():
    _with_auth_override()
    response = client.post(
        "/api/v1/match-job/file",
        data={"job_description": "Python dev"},
        files={"file": ("test.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_match_job_file_no_description():
    _with_auth_override()
    response = client.post(
        "/api/v1/match-job/file",
        files={"file": ("test.pdf", b"PDF content", "application/pdf")},
    )
    assert response.status_code == 422


def test_tailor_resume_requires_auth():
    response = client.post("/api/v1/tailor-resume", json={})
    assert response.status_code == 401


def test_stand_out_requires_auth():
    response = client.post("/api/v1/stand-out", json={})
    assert response.status_code == 401


def test_cover_letter_requires_auth():
    response = client.post("/api/v1/cover-letter", json={})
    assert response.status_code == 401


def test_rewrite_suggestions_requires_auth():
    response = client.post("/api/v1/rewrite-suggestions", json={})
    assert response.status_code == 401


def test_skills_market_demand_requires_auth():
    response = client.get("/api/v1/skills/market-demand")
    assert response.status_code == 401


# --- Protected endpoint validation tests (with auth override) ---


def test_match_job_validation_error():
    _with_auth_override()
    response = client.post("/api/v1/match-job", json={})
    assert response.status_code == 422


def test_tailor_resume_validation_error():
    _with_auth_override()
    response = client.post("/api/v1/tailor-resume", json={})
    assert response.status_code == 422


def test_stand_out_validation_error():
    _with_auth_override()
    response = client.post("/api/v1/stand-out", json={})
    assert response.status_code == 422


def test_cover_letter_validation_error():
    _with_auth_override()
    response = client.post("/api/v1/cover-letter", json={})
    assert response.status_code == 422


def test_rewrite_suggestions_validation_error():
    _with_auth_override()
    response = client.post("/api/v1/rewrite-suggestions", json={})
    assert response.status_code == 422
