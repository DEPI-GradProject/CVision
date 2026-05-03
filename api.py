import os
import pandas as pd
from fastapi import FastAPI
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
    title="CVision Jobs API",
    description="API to provide clean tech jobs data for the CVision Chatbot",
    version="1.0.0"
)

# --- 3. API Endpoints ---

@app.get("/")
def home():
    return {"message": "Welcome to CVision API! Everything is running perfectly 🚀"}

@app.get("/api/v1/jobs/latest")
def get_latest_jobs(limit: int = 50):

        # This endpoint fetches the latest jobs from the 'jobs_raw' table, ordered by published_date (assuming such a column exists). It returns the data in a JSON format that can be easily consumed by the frontend or the AI model
    try:
        # arrange the query to get the latest jobs based on published_date (assuming there's a column named published_date)
        query = f"SELECT * FROM jobs_raw ORDER BY published_date DESC LIMIT {limit}"
        df = pd.read_sql(query, engine)
        
        # convert the date to a string to avoid JSON serialization errors
        if 'published_date' in df.columns:
            df['published_date'] = df['published_date'].astype(str)
            
        # convert the data to a JSON-compatible format
        jobs_data = df.to_dict(orient="records")
        
        return {
            "status": "success",
            "total_returned": len(jobs_data),
            "data": jobs_data
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/v1/jobs/training")
def get_training_data(limit: int = 100):

    try:
        query = f"SELECT * FROM training_jobs LIMIT {limit}"
        df = pd.read_sql(query, engine)
        training_data = df.to_dict(orient="records")
        
        return {
            "status": "success",
            "total_returned": len(training_data),
            "data": training_data
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}   