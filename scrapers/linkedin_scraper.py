import logging
import time
from datetime import datetime

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import settings
from db_setup import RawJob

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

engine = create_engine(settings.database_url_with_ssl)
Session = sessionmaker(bind=engine)
session = Session()


def setup_driver():
    chrome_options = Options()

    if settings.chrome_browser_path:
        chrome_options.binary_location = settings.chrome_browser_path

    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=chrome_options)
    return driver


def scrape_linkedin_jobs(keyword, location=None):
    location = location or settings.linkedin_location
    logger.info("=" * 50)
    logger.info("[%s] Starting Scraper...", keyword)
    logger.info("=" * 50)

    driver = setup_driver()

    encoded_keyword = keyword.replace(" ", "%20")
    encoded_location = location.replace(" ", "%20")
    search_url = f"https://www.linkedin.com/jobs/search?keywords={encoded_keyword}&location={encoded_location}"
    driver.get(search_url)

    scroll_pause = settings.scroll_pause_seconds
    max_scrolls = settings.max_scrolls

    logger.info("Waiting 10 seconds for initial page load...")
    time.sleep(10)

    logger.info("Scrolling and bypassing 'See more jobs' button...")
    last_height = driver.execute_script("return document.body.scrollHeight")

    for i in range(max_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        logger.info("  -> Scroll %s/%s... waiting %s seconds", i + 1, max_scrolls, scroll_pause)
        time.sleep(scroll_pause)

        try:
            see_more_btn = driver.find_element(By.CSS_SELECTOR, "button.infinite-scroller__show-more-button")
            if see_more_btn.is_displayed():
                logger.info("  -> Clicking 'See more jobs' button...")
                driver.execute_script("arguments[0].click();", see_more_btn)
                time.sleep(scroll_pause)
        except Exception:
            pass

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            logger.info("  -> Hit the bottom, waiting 10 extra seconds...")
            time.sleep(10)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                logger.info("  -> No more new jobs loading. Stopping scroll.")
                break
        last_height = new_height

    final_wait = settings.final_wait_seconds
    logger.info("Scrolling done! Waiting %s seconds for rendering...", final_wait)
    time.sleep(final_wait)

    logger.info("Extracting data...")
    soup = BeautifulSoup(driver.page_source, "html.parser")
    job_cards = soup.find_all("div", class_="base-card")
    logger.info("Found %s job cards for %s. Saving to database...", len(job_cards), keyword)

    new_jobs_count = 0
    for card in job_cards:
        try:
            title_tag = card.find("h3", class_="base-search-card__title")
            link_tag = card.find("a", class_="base-card__full-link")

            if not title_tag or not link_tag:
                continue

            title = title_tag.text.strip()
            link = link_tag["href"].split("?")[0]

            company_tag = card.find("h4", class_="base-search-card__subtitle")
            company = company_tag.text.strip() if company_tag else "Unknown"
            description = f"Company: {company}"

            exists = session.query(RawJob).filter_by(job_link=link).first()
            if not exists:
                new_job = RawJob(
                    platform="LinkedIn",
                    job_title=title,
                    job_link=link,
                    description=description,
                    published_date=datetime.now(),
                )
                session.add(new_job)
                new_jobs_count += 1

        except Exception:
            continue

    session.commit()
    driver.quit()
    logger.info("Success! Added %s NEW jobs for %s.", new_jobs_count, keyword)


if __name__ == "__main__":
    tech_keywords = [
        "Software Engineer",
        "Data Scientist",
        "Machine Learning",
        "Frontend Developer",
        "Backend Developer",
        "Full Stack",
        "DevOps",
        "AI Engineer",
        "Data Analyst",
        "Cyber Security",
        "Mobile Developer",
        "Flutter",
        "React",
        "Python Developer",
        "UI UX Designer",
    ]

    for kw in tech_keywords:
        scrape_linkedin_jobs(kw)
