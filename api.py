import os
import pandas as pd
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from dotenv import load_dotenv

# --- 1. Database Connection ---
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if "sslmode=" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

engine = create_engine(DATABASE_URL)

# --- 2. Create API App ---
app = FastAPI(
    title="CVision Core API",
    description="Backend infrastructure for job data and CV processing",
    version="1.1.0"
)

# --- 3. CORS Configuration so the frontend can access this API without issues (you can adjust the allowed origins in production for better security) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #make any origin can access this API (you can specify your frontend URL here in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 4. API Endpoints ---

@app.get("/")
def home():
    return {"message": "CVision API is Online 🚀"}

# the path for this endpoint is /api/v1/jobs/latest and it accepts an optional query parameter 'limit' to specify how many of the latest jobs to return (default is 50 if not provided). It fetches the latest jobs from the 'jobs_raw' table in the database, ordered by published_date in descending order, and returns them as a JSON response. If there's an error during the database query, it returns an error message instead.
@app.get("/api/v1/jobs/latest")
def get_latest_jobs(limit: int = 50):
    try:
        query = f"SELECT * FROM jobs_raw ORDER BY published_date DESC LIMIT {limit}"
        df = pd.read_sql(query, engine)
        if 'published_date' in df.columns:
            df['published_date'] = df['published_date'].astype(str)
        return {"status": "success", "data": df.to_dict(orient="records")}
    except Exception as e:
        return {"status": "error", "message": str(e)}
# the path for this endpoint is /api/v1/jobs/training and it also accepts an optional 'limit' query parameter to specify how many training job records to return (default is 100). It queries the 'training_jobs' table in the database, retrieves the specified number of records, and returns them as a JSON response. If there's an error during the database query, it returns an error message instead.
@app.get("/api/v1/jobs/training")
def get_training_data(limit: int = 100):
    try:
        query = f"SELECT * FROM training_jobs LIMIT {limit}"
        df = pd.read_sql(query, engine)
        return {"status": "success", "data": df.to_dict(orient="records")}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# path for this endpoint is /api/v1/analyze-cv and it accepts a POST request with a file upload (specifically a PDF file). The endpoint is designed to receive the CV file from the user, and it's where your AI Matcher will eventually be integrated to analyze the CV against the job data. For now, it simply returns a success message confirming that the CV file was received, along with the filename and a note that the AI Matcher is ready for integration. If there's an error during file reception, it returns an error message instead.
@app.post("/api/v1/analyze-cv")
async def analyze_cv(file: UploadFile = File(...)):
    """
    here we receive the PDF file from the user.
    your AI colleague will integrate their agents here.
    """
    try:
        # temporarily return a success message
        return {
            "status": "success",
            "filename": file.filename,
            "message": "CV file received. AI Matcher is ready for integration."
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}