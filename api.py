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

