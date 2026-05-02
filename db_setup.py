# db_setup.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base

# Load environment variables from .env file
load_dotenv()

# Get database connection string
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing. Please check your .env file.")

# Create the SQLAlchemy engine
# Supabase sometimes requires sslmode=require for remote connections
if "sslmode=" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

engine = create_engine(DATABASE_URL, echo=True)

# Define the declarative base
Base = declarative_base()

# Define the Jobs table schema
class RawJob(Base):
    __tablename__ = 'jobs_raw'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(50), nullable=False)
    job_title = Column(String(255), nullable=False)
    job_link = Column(String, unique=True, nullable=False) # Unique to prevent duplicates
    description = Column(Text, nullable=True)
    published_date = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<RawJob(platform='{self.platform}', title='{self.job_title}')>"

# Create the table in the database
def init_db():
    print("Connecting to Supabase Database...")
    try:
        Base.metadata.create_all(engine)
        print("Table 'jobs_raw' created successfully (if it didn't already exist).")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    init_db()