import asyncio
import json
import logging
import os
import tempfile
from datetime import UTC, datetime

import pandas as pd
import sentry_sdk
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from auth import auth_backend, current_active_user, fastapi_users
from config import settings
from graph.workflow import graph
from models.db_models import AnalysisHistory, User
from models.schemas import AgentState

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

engine = create_engine(settings.database_url_with_ssl)
SessionLocal = sessionmaker(bind=engine)

app = FastAPI(
    title="CVision Core API", description="Backend infrastructure for job data and CV processing", version="0.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        environment="production",
    )
    logger.info("Sentry initialized")

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


class UserRead(BaseModel):
    id: int
    email: str
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    is_verified: bool | None = None
    password: str | None = None


def _save_analysis(user_id: int, filename: str, ats_score: int | None, skills: list[str], job_matches: int):
    db = SessionLocal()
    try:
        record = AnalysisHistory(
            user_id=user_id,
            filename=filename,
            ats_score=ats_score,
            skills_extracted=json.dumps(skills),
            job_matches=job_matches,
            created_at=datetime.now(UTC),
        )
        db.add(record)
        db.commit()
    except Exception as e:
        logger.error("Failed to save analysis history: %s", e)
        db.rollback()
    finally:
        db.close()


app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/auth",
    tags=["auth"],
)


@app.get("/")
def home():
    return {"message": "CVision API is Online"}


@app.get("/api/v1/health")
@limiter.limit("30/minute")
def health(request: Request):
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        pass
    return {"status": "healthy" if db_ok else "degraded", "database": "connected" if db_ok else "disconnected"}


@app.get("/api/v1/jobs/latest")
@limiter.limit("30/minute")
def get_latest_jobs(request: Request, limit: int = 50):
    try:
        query = text("SELECT * FROM jobs_raw ORDER BY published_date DESC LIMIT :limit")
        df = pd.read_sql(query, engine, params={"limit": limit})
        if "published_date" in df.columns:
            df["published_date"] = df["published_date"].astype(str)
        return {"status": "success", "data": df.to_dict(orient="records")}
    except Exception as e:
        logger.error("Failed to fetch latest jobs: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/jobs/training")
@limiter.limit("30/minute")
def get_training_data(request: Request, limit: int = 100):
    try:
        query = text("SELECT * FROM training_jobs LIMIT :limit")
        df = pd.read_sql(query, engine, params={"limit": limit})
        return {"status": "success", "data": df.to_dict(orient="records")}
    except Exception as e:
        logger.error("Failed to fetch training data: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/history")
@limiter.limit("30/minute")
def get_analysis_history(request: Request, user: User = Depends(current_active_user), limit: int = 50):
    try:
        db = SessionLocal()
        try:
            records = (
                db.query(AnalysisHistory)
                .filter(AnalysisHistory.user_id == user.id)
                .order_by(AnalysisHistory.created_at.desc())
                .limit(limit)
                .all()
            )
            data = []
            for r in records:
                data.append(
                    {
                        "id": r.id,
                        "filename": r.filename,
                        "ats_score": r.ats_score,
                        "skills_extracted": json.loads(r.skills_extracted) if r.skills_extracted else [],
                        "job_matches": r.job_matches,
                        "created_at": r.created_at.isoformat(),
                    }
                )
            return {"status": "success", "data": data}
        finally:
            db.close()
    except Exception as e:
        logger.error("Failed to fetch analysis history: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/stats")
@limiter.limit("30/minute")
def get_analysis_stats(request: Request, user: User = Depends(current_active_user)):
    try:
        db = SessionLocal()
        try:
            records = db.query(AnalysisHistory).filter(AnalysisHistory.user_id == user.id).all()
            total = len(records)
            scores = [r.ats_score for r in records if r.ats_score is not None]
            avg_score = round(sum(scores) / len(scores)) if scores else 0
            total_matches = sum(r.job_matches or 0 for r in records)
            last = max((r.created_at for r in records), default=None)

            if last:
                delta = datetime.now(UTC) - last
                if delta.days > 0:
                    last_str = f"{delta.days}d ago"
                elif delta.seconds // 3600 > 0:
                    last_str = f"{delta.seconds // 3600}h ago"
                else:
                    last_str = f"{delta.seconds // 60}m ago"
            else:
                last_str = "N/A"

            return {
                "status": "success",
                "data": {
                    "total_analyses": total,
                    "average_score": avg_score,
                    "total_job_matches": total_matches,
                    "last_analysis": last_str,
                },
            }
        finally:
            db.close()
    except Exception as e:
        logger.error("Failed to fetch stats: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/v1/analyze-cv")
@limiter.limit("5/minute")
async def analyze_cv(request: Request, file: UploadFile = File(...), user: User = Depends(current_active_user)):
    allowed_extensions = {"pdf", "docx"}
    ext = file.filename.split(".")[-1].lower() if file.filename else ""

    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: .{ext}. Use PDF or DOCX.")

    try:
        contents = await file.read()
        file_size = len(contents)
        max_size = 10 * 1024 * 1024
        if file_size > max_size:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

        logger.info("CV received: %s (%s bytes)", file.filename, file_size)

        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        try:
            state = AgentState(file_path=tmp_path, file_name=file.filename)
            result = graph.invoke(state)

            if result.error:
                raise HTTPException(status_code=500, detail=result.error)

            ats_score = result.analysis.ats_result.ats_score if result.analysis and result.analysis.ats_result else None
            skills = result.analysis.skills_extracted if result.analysis else []
            job_matches = len(result.job_matches.matched_jobs) if result.job_matches else 0
            _save_analysis(user.id, file.filename, ats_score, skills, job_matches)

            return {
                "status": "success",
                "filename": file.filename,
                "ats_score": ats_score,
                "skills_extracted": skills,
                "job_matches": job_matches,
                "report": result.final_report,
            }
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error processing CV: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


def _run_pipeline(file_path: str, file_name: str, user_id: int | None = None):
    try:
        state = AgentState(file_path=file_path, file_name=file_name)

        for node_name, step_output in graph.stream(state):
            step = node_name.removeprefix("cv_").removeprefix("_")
            if step_output.get("error"):
                yield f"data: {json.dumps({'step': 'error', 'error': step_output['error']})}\n\n"
                return
            yield f"data: {json.dumps({'step': step, 'status': 'complete'})}\n\n"

        result = step_output
        if result.error:
            yield f"data: {json.dumps({'step': 'error', 'error': result.error})}\n\n"
            return

        ats_score = result.analysis.ats_result.ats_score if result.analysis and result.analysis.ats_result else None
        skills = result.analysis.skills_extracted if result.analysis else []
        job_matches = len(result.job_matches.matched_jobs) if result.job_matches else 0

        if user_id is not None:
            _save_analysis(user_id, file_name, ats_score, skills, job_matches)

        payload = json.dumps(
            {
                "step": "complete",
                "result": {
                    "filename": file_name,
                    "ats_score": ats_score,
                    "skills_extracted": skills,
                    "job_matches": job_matches,
                    "report": result.final_report,
                },
            }
        )
        yield f"data: {payload}\n\n"

    except Exception as e:
        logger.error("Pipeline error: %s", e)
        yield f"data: {json.dumps({'step': 'error', 'error': str(e)})}\n\n"


@app.post("/api/v1/analyze-cv/stream")
@limiter.limit("5/minute")
async def analyze_cv_stream(request: Request, file: UploadFile = File(...), user: User = Depends(current_active_user)):
    allowed_extensions = {"pdf", "docx"}
    ext = file.filename.split(".")[-1].lower() if file.filename else ""

    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: .{ext}. Use PDF or DOCX.")

    contents = await file.read()
    file_size = len(contents)
    max_size = 10 * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

    logger.info("CV stream received: %s (%s bytes)", file.filename, file_size)

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    async def event_generator():
        try:
            loop = asyncio.get_event_loop()
            for event in await loop.run_in_executor(None, _run_pipeline, tmp_path, file.filename, user.id):
                yield event
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
