import asyncio
import json
import logging
import os
import tempfile

import pandas as pd
import sentry_sdk
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import create_engine, text

from config import settings
from graph.workflow import graph
from models.schemas import AgentState

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

engine = create_engine(settings.database_url_with_ssl)

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
        logger.error("Failed to fetch latest jobs: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/jobs/training")
@limiter.limit("30/minute")
def get_training_data(request: Request, limit: int = 100):
    try:
        query = text("SELECT * FROM training_jobs LIMIT :limit")
        df = pd.read_sql(query, engine, params={"limit": limit})
        return {"status": "success", "data": df.to_dict(orient="records")}
    except Exception as e:
        logger.error("Failed to fetch training data: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/analyze-cv")
@limiter.limit("5/minute")
async def analyze_cv(request: Request, file: UploadFile = File(...)):
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

            return {
                "status": "success",
                "filename": file.filename,
                "ats_score": result.analysis.ats_result.ats_score
                if result.analysis and result.analysis.ats_result
                else None,
                "skills_extracted": result.analysis.skills_extracted if result.analysis else [],
                "job_matches": len(result.job_matches.matched_jobs) if result.job_matches else 0,
                "report": result.final_report,
            }
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error processing CV: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


def _run_pipeline(file_path: str, file_name: str):
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

        payload = json.dumps(
            {
                "step": "complete",
                "result": {
                    "filename": file_name,
                    "ats_score": result.analysis.ats_result.ats_score
                    if result.analysis and result.analysis.ats_result
                    else None,
                    "skills_extracted": result.analysis.skills_extracted if result.analysis else [],
                    "job_matches": len(result.job_matches.matched_jobs) if result.job_matches else 0,
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
async def analyze_cv_stream(request: Request, file: UploadFile = File(...)):
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
            for event in await loop.run_in_executor(None, _run_pipeline, tmp_path, file.filename):
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
