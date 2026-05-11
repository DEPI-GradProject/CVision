import logging
from datetime import datetime

import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import settings
from db_setup import RawJob

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

engine = create_engine(settings.database_url_with_ssl)
Session = sessionmaker(bind=engine)
session = Session()


def fetch_all_tech_jobs():
    logger.info("Starting Tech Jobs Scraper (All Software Categories)...")

    api_url = "https://remotive.com/api/remote-jobs"

    try:
        response = requests.get(api_url, timeout=30)
        if response.status_code != 200:
            logger.error("Failed to fetch from API. Status code: %s", response.status_code)
            return

        data = response.json()
        jobs_list = data.get("jobs", [])
        logger.info("Found %s tech jobs! Checking for new ones...", len(jobs_list))

        new_jobs_count = 0

        for job in jobs_list:
            title = job.get("title", "")
            link = job.get("url", "")
            description = job.get("description", "")
            platform = "Remotive (Global Tech)"

            pub_date_str = job.get("publication_date", "")
            try:
                pub_date = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
            except Exception:
                pub_date = datetime.now()

            exists = session.query(RawJob).filter_by(job_link=link).first()

            if not exists:
                new_job = RawJob(
                    platform=platform, job_title=title, job_link=link, description=description, published_date=pub_date
                )
                session.add(new_job)
                new_jobs_count += 1

                if new_jobs_count <= 10:
                    logger.info("[NEW] Added: %s...", title[:50])

        session.commit()
        logger.info("Scraping complete! Added %s NEW tech jobs to the database.", new_jobs_count)

    except requests.RequestException as e:
        logger.error("Request failed: %s", e)
        session.rollback()
    except Exception as e:
        logger.error("An error occurred: %s", e)
        session.rollback()


if __name__ == "__main__":
    fetch_all_tech_jobs()
