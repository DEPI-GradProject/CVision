import logging
import os
import pandas as pd
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if "sslmode=" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

engine = create_engine(DATABASE_URL)

app = FastAPI(
    title="CVision Core API",
    description="Backend infrastructure for job data and CV processing",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "CVision API is Online"}


@app.get("/api/v1/jobs/latest")
def get_latest_jobs(limit: int = 50):
    try:
        query = text("SELECT * FROM jobs_raw ORDER BY published_date DESC LIMIT :limit")
        df = pd.read_sql(query, engine, params={"limit": limit})
        if 'published_date' in df.columns:
            df['published_date'] = df['published_date'].astype(str)
        return {"status": "success", "data": df.to_dict(orient="records")}
    except Exception as e:
        logger.error("Failed to fetch latest jobs: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/jobs/training")
def get_training_data(limit: int = 100):
    try:
        query = text("SELECT * FROM training_jobs LIMIT :limit")
        df = pd.read_sql(query, engine, params={"limit": limit})
        return {"status": "success", "data": df.to_dict(orient="records")}
    except Exception as e:
        logger.error("Failed to fetch training data: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/analyze-cv")
async def analyze_cv(file: UploadFile = File(...)):
    ALLOWED_EXTENSIONS = {"pdf", "docx"}
    ext = file.filename.split(".")[-1].lower() if file.filename else ""

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: .{ext}. Use PDF or DOCX.")

    try:
        contents = await file.read()
        file_size = len(contents)
        MAX_SIZE = 10 * 1024 * 1024
        if file_size > MAX_SIZE:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

        logger.info("CV received: %s (%s bytes)", file.filename, file_size)

        return {
            "status": "success",
            "filename": file.filename,
            "size_bytes": file_size,
            "message": "CV file received. AI Matcher is ready for integration."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error processing CV upload: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
