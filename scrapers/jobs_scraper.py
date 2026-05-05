# tech_jobs_scraper.py
import requests
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_setup import RawJob  
from datetime import datetime

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if "sslmode=" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

# Connect to Database
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

def fetch_all_tech_jobs():
    print("Starting Tech Jobs Scraper (All Software Categories)...")
    
    # Api endpoint for remote tech jobs from Remotive (covers all software categories globally)
    api_url = "https://remotive.com/api/remote-jobs"
    
    try:
        response = requests.get(api_url)
        if response.status_code != 200:
            print(f"Failed to fetch from API. Status code: {response.status_code}")
            return
            
        data = response.json()
        jobs_list = data.get('jobs', [])
        print(f"Found {len(jobs_list)} tech jobs! Checking for new ones...")

        new_jobs_count = 0
        
        for job in jobs_list:
            title = job.get('title', '')
            link = job.get('url', '')
            description = job.get('description', '')
            platform = "Remotive (Global Tech)"
            
            # making the date parsing more robust by using fromisoformat and handling exceptions (since some APIs might have different date formats or missing dates)
            pub_date_str = job.get('publication_date', '')
            try:
                # the API might return dates in ISO format, but sometimes it could be missing or in a different format, so we handle that gracefully
                pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
            except Exception:
                pub_date = datetime.now()

            # ensure we don't add duplicate jobs based on the unique job link (assuming the API provides a unique URL for each job). This prevents cluttering the database with duplicates if we run the scraper multiple times.
            exists = session.query(RawJob).filter_by(job_link=link).first()
            
            if not exists:
                new_job = RawJob(
                    platform=platform,
                    job_title=title,
                    job_link=link,
                    description=description,
                    published_date=pub_date
                )
                session.add(new_job)
                new_jobs_count += 1
                
                # check some of the new jobs and print them out (but only the first 10 to avoid flooding the console)
                if new_jobs_count <= 10:
                    print(f"  [NEW] Added: {title[:50]}...")
                
        # saving all the new jobs to the database at once after the loop is more efficient than committing inside the loop. This way we reduce the number of transactions and speed up the process, especially if there are many new jobs.
        session.commit()
        print(f"\nScraping complete! Added {new_jobs_count} NEW tech jobs to the database.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        session.rollback()

if __name__ == "__main__":
    fetch_all_tech_jobs()