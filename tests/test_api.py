import asyncio
import os
from unittest.mock import Mock, patch

import pytest

pytest.importorskip("sqlalchemy")
pytest.importorskip("fastapi")
pytest.importorskip("langgraph")

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["AUTH_JWT_SECRET"] = "test-secret-for-ci"

from datetime import UTC

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


# --- Auth rate limit (line 113) ---


def _clean_history_for_user(user_id: int):
    from api import SessionLocal
    from models.db_models import AnalysisHistory

    db = SessionLocal()
    try:
        db.query(AnalysisHistory).filter(AnalysisHistory.user_id == user_id).delete()
        db.commit()
    finally:
        db.close()


def test_auth_rate_limit_429():
    for _ in range(11):
        response = client.post(
            "/auth/register",
            json={"email": "ratelimit@test.com", "password": "Str0ng!Pass"},
        )
        if response.status_code == 400:
            response = client.post(
                "/auth/login",
                data={"username": "ratelimit@test.com", "password": "Str0ng!Pass"},
            )
    assert response.status_code == 429
    assert "Too many auth attempts" in response.json()["detail"]


# --- Jobs endpoints with data (lines 214-231) ---


def test_latest_jobs_with_data():
    from datetime import datetime

    from api import SessionLocal
    from models.db_models import RawJob

    db = SessionLocal()
    try:
        db.add(
            RawJob(
                platform="test",
                job_title="Python Dev",
                job_link="http://example.com/job1",
                published_date=datetime.now(UTC),
            )
        )
        db.commit()
    finally:
        db.close()

    response = client.get("/api/v1/jobs/latest?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["data"]) >= 1
    assert data["data"][0]["job_title"] == "Python Dev"


def test_training_data_with_data():
    from api import SessionLocal
    from models.db_models import TrainingJob

    db = SessionLocal()
    try:
        db.add(TrainingJob(Title="Learn Python", Skills="Python", platform_source="test"))
        db.commit()
    finally:
        db.close()

    response = client.get("/api/v1/jobs/training?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["data"]) >= 1


# --- History with records (line 252) ---


def test_history_with_records():
    _with_auth_override()
    _clean_history_for_user(1)
    from datetime import datetime

    from api import SessionLocal
    from models.db_models import AnalysisHistory

    db = SessionLocal()
    try:
        db.add(
            AnalysisHistory(
                user_id=1,
                filename="test.pdf",
                ats_score=85,
                skills_extracted='["python"]',
                job_matches=3,
                created_at=datetime.now(UTC),
            )
        )
        db.commit()
    finally:
        db.close()

    response = client.get("/api/v1/history")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["data"]) >= 1
    assert data["data"][0]["filename"] == "test.pdf"
    assert data["data"][0]["ats_score"] == 85


# --- Stats with time deltas (lines 286-294) ---


def _insert_stats_record(ats_score: int, **td_kwargs):
    from datetime import datetime, timedelta

    from api import SessionLocal
    from models.db_models import AnalysisHistory

    _clean_history_for_user(1)
    db = SessionLocal()
    try:
        created = datetime.now(UTC) - timedelta(**td_kwargs) if td_kwargs else datetime.now(UTC)
        db.add(
            AnalysisHistory(
                user_id=1,
                filename="stats_test.pdf",
                ats_score=ats_score,
                skills_extracted='["python"]',
                job_matches=1,
                created_at=created,
            )
        )
        db.commit()
    finally:
        db.close()


def test_stats_days_ago():
    _with_auth_override()
    _insert_stats_record(90, days=5)
    response = client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert "5d ago" in data["data"]["last_analysis"]


def test_stats_hours_ago():
    _with_auth_override()
    _insert_stats_record(80, hours=3)
    response = client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert "h ago" in data["data"]["last_analysis"]
    assert "d ago" not in data["data"]["last_analysis"]


def test_stats_minutes_ago():
    _with_auth_override()
    _insert_stats_record(70)
    response = client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert "m ago" in data["data"]["last_analysis"]


# --- Market skill demand (requires PostgreSQL ILIKE, skip on SQLite) ---


def test_market_skill_demand_with_data():
    _with_auth_override()

    from api import SessionLocal
    from models.db_models import RawJob

    db = SessionLocal()
    try:
        for i in range(15):
            db.add(
                RawJob(
                    platform="test",
                    job_title=f"Job {i}",
                    job_link=f"http://example.com/job_{i}",
                    description="We need Python, SQL, and Docker skills",
                )
            )
        db.commit()
    finally:
        db.close()

    response = client.get("/api/v1/skills/market-demand")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["data"]) > 0
    python_skill = next((s for s in data["data"] if s["skill"] == "Python"), None)
    assert python_skill is not None
    assert python_skill["job_count"] >= 15
    assert python_skill["demand_level"] == "high"


# --- LLM endpoint tests (patch _get_*_llm to return controlled mocks) ---


def _mock_llm_response_for(api_func: str, json_str: str):
    """Patch a _get_*_llm function so the endpoint returns controlled data."""
    mock_llm = Mock(spec=LLM)
    mock_llm.invoke.return_value = json_str
    patcher = patch(f"api.{api_func}", return_value=mock_llm)
    patcher.start()
    return patcher


def test_tailor_resume_success():
    _with_auth_override()
    patcher = _mock_llm_response_for("_get_tailor_llm", "Rewritten CV text for the job")
    try:
        response = client.post(
            "/api/v1/tailor-resume",
            json={"cv_text": "Experienced dev", "job_description": "Need dev"},
        )
        assert response.status_code == 200
        assert response.json()["tailored_resume"] == "Rewritten CV text for the job"
    finally:
        patcher.stop()


def test_tailor_resume_empty_response():
    _with_auth_override()
    patcher = _mock_llm_response_for("_get_tailor_llm", "")
    try:
        response = client.post(
            "/api/v1/tailor-resume",
            json={"cv_text": "Experienced dev", "job_description": "Need dev"},
        )
        assert response.status_code == 500
    finally:
        patcher.stop()


def test_stand_out_success():
    _with_auth_override()
    payload = (
        '{"unique_selling_points": ["ML expert"],'
        ' "suggested_certifications": ["AWS"],'
        ' "project_ideas": ["Build a chatbot"],'
        ' "skill_enhancements": ["Kubernetes"],'
        ' "overall_strategy": "Focus on AI"}'
    )
    patcher = _mock_llm_response_for("_get_standout_llm", payload)
    try:
        response = client.post(
            "/api/v1/stand-out",
            json={"cv_text": "ML engineer", "job_description": "AI role"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["unique_selling_points"] == ["ML expert"]
        assert data["overall_strategy"] == "Focus on AI"
    finally:
        patcher.stop()


def test_cover_letter_success():
    _with_auth_override()
    patcher = _mock_llm_response_for(
        "_get_cover_llm", "Dear Hiring Manager,\n\nI am perfect for this role.\n\nSincerely,\nMe"
    )
    try:
        response = client.post(
            "/api/v1/cover-letter",
            json={"cv_text": "Experienced", "job_description": "Job desc"},
        )
        assert response.status_code == 200
        assert "Dear Hiring Manager" in response.json()["cover_letter"]
    finally:
        patcher.stop()


def test_rewrite_suggestions_success():
    _with_auth_override()
    payload = (
        '{"overall_assessment": "Good CV",'
        ' "rewrites": [{"original": "Did stuff", "issue": "Too vague", "improved": "Led team"}],'
        ' "quick_wins": ["Add numbers"]}'
    )
    patcher_llm = _mock_llm_response_for("_get_rewrite_llm", payload)
    patcher_pdf = patch("api.extract_text_from_pdf", return_value="Extracted CV text with skills")
    patcher_pdf.start()
    try:
        response = client.post(
            "/api/v1/rewrite-suggestions",
            files={"file": ("test.pdf", b"PDF content", "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["overall_assessment"] == "Good CV"
        assert len(data["rewrites"]) == 1
        assert data["quick_wins"] == ["Add numbers"]
    finally:
        patcher_llm.stop()
        patcher_pdf.stop()


def test_rewrite_suggestions_wrong_extension():
    _with_auth_override()
    response = client.post(
        "/api/v1/rewrite-suggestions",
        files={"file": ("test.exe", b"binary data", "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_rewrite_suggestions_too_large():
    _with_auth_override()
    response = client.post(
        "/api/v1/rewrite-suggestions",
        files={"file": ("test.pdf", b"x" * (11 * 1024 * 1024), "application/pdf")},
    )
    assert response.status_code == 400
    assert "too large" in response.json()["detail"].lower()


def test_match_job_file_success():
    _with_auth_override()
    patcher_llm = _mock_llm_response_for(
        "_get_match_llm",
        '{"match_score": 85, "matched_skills": ["python"],'
        ' "missing_skills": ["docker"],'
        ' "improvement_tips": ["Learn Docker"],'
        ' "keyword_coverage": 0.7}',
    )
    patcher_pdf = patch("api.extract_text_from_pdf", return_value="Python developer with ML experience")
    patcher_pdf.start()
    try:
        response = client.post(
            "/api/v1/match-job/file",
            data={"job_description": "Python dev with Docker"},
            files={"file": ("test.pdf", b"PDF content", "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["match_score"] == 85
        assert "python" in data["matched_skills"]
    finally:
        patcher_llm.stop()
        patcher_pdf.stop()


def test_match_job_file_too_large():
    _with_auth_override()
    response = client.post(
        "/api/v1/match-job/file",
        data={"job_description": "Python dev"},
        files={"file": ("test.pdf", b"x" * (11 * 1024 * 1024), "application/pdf")},
    )
    assert response.status_code == 400
    assert "too large" in response.json()["detail"].lower()


# --- analyze-cv stream endpoint ---


def test_analyze_cv_stream_success():
    _with_auth_override()
    fake_events = [
        'data: {"step":"parse","status":"complete"}\n\n',
        'data: {"step":"analyze","status":"complete"}\n\n',
        'data: {"step":"complete",'
        '"result":{"ats_score":90,"skills_extracted":["python"],'
        '"job_matches":2,"matched_jobs":[],"report":"Great CV"}}\n\n',
    ]

    with patch("api._run_pipeline") as mock_pipeline:
        mock_pipeline.return_value = fake_events
        response = client.post(
            "/api/v1/analyze-cv/stream",
            files={"file": ("test.pdf", b"PDF content", "application/pdf")},
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        text = response.text
        assert "parse" in text
        assert "analyze" in text
        assert "ats_score" in text


# --- _run_pipeline generator ---


def test_run_pipeline_yields_events():
    from api import _run_pipeline

    fake_state = {
        "analysis": type(
            "Analysis", (), {"ats_result": type("ATS", (), {"ats_score": 80})(), "skills_extracted": ["python"]}
        )(),
        "job_matches": type("Jobs", (), {"matched_jobs": []})(),
        "final_report": "OK",
        "error": None,
    }

    stream_steps = [
        {"cv_parser": type("S1", (), {"error": None})()},
        {"cv_analyzer": type("S2", (), {"error": None})()},
        {"job_matcher": type("S3", (), {"error": None})()},
        {"report_builder": fake_state},
    ]

    with patch("api.graph.stream", return_value=iter(stream_steps)):
        events = list(_run_pipeline("/tmp/test.pdf", "test.pdf", user_id=1))

    assert len(events) >= 4
    # first event
    assert events[0].startswith("data: ")
    assert "parser" in events[0] or "parse" in events[0]


def test_run_pipeline_yields_error_event():
    from api import _run_pipeline

    error_state = type("ES", (), {"error": "Parsing failed"})()
    stream_steps = [{"cv_parser": error_state}]

    with patch("api.graph.stream", return_value=iter(stream_steps)):
        events = list(_run_pipeline("/tmp/test.pdf", "test.pdf"))

    assert len(events) == 1
    assert '"error"' in events[0]
    assert "Parsing failed" in events[0]


# --- Input validation (max_length) ---


def test_match_job_cv_text_too_long():
    _with_auth_override()
    response = client.post(
        "/api/v1/match-job",
        json={"cv_text": "x" * 100001, "job_description": "short"},
    )
    assert response.status_code == 422


def test_match_job_description_too_long():
    _with_auth_override()
    response = client.post(
        "/api/v1/match-job",
        json={"cv_text": "short", "job_description": "x" * 50001},
    )
    assert response.status_code == 422


def test_cover_letter_cv_text_too_long():
    _with_auth_override()
    response = client.post(
        "/api/v1/cover-letter",
        json={"cv_text": "x" * 100001, "job_description": "short"},
    )
    assert response.status_code == 422
