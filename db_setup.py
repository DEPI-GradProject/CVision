# db_setup.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base

from config import settings

if not settings.database_url:
    raise ValueError("DATABASE_URL is missing. Please check your .env file.")

engine = create_engine(settings.database_url_with_ssl, echo=True)

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