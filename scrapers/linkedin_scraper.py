import time
import os
from datetime import datetime
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_setup import RawJob 

# --- 1. Database Setup ---
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if "sslmode=" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# --- 2. Selenium Setup (Brave Browser) ---
def setup_driver():
    chrome_options = Options()
    chrome_options.binary_location = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    
    # so the browser runs in the background without opening a window (headless mode)
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

# --- 3. Advanced Scraping Logic ---
def scrape_linkedin_jobs(keyword, location="Egypt"):
    print(f"\n{'='*50}\n[{keyword}] Starting Scraper...\n{'='*50}")
    driver = setup_driver()
    
    search_url = f"https://www.linkedin.com/jobs/search?keywords={keyword.replace(' ', '%20')}&location={location.replace(' ', '%20')}"
    driver.get(search_url)
    
    print("Waiting 10 seconds for initial page load...")
    time.sleep(10)
    
    print("Scrolling and bypassing 'See more jobs' button...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    # scorlling about 25 times with waits in between to allow jobs to load (you can adjust the number of scrolls and wait times based on how many jobs you want to load and how fast the page loads)
    for i in range(25): 
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print(f"  -> Scroll {i+1}/25... waiting 5 seconds for jobs to load")
        time.sleep(5) #longer wait time to allow more jobs to load
        
        try:
            see_more_btn = driver.find_element(By.CSS_SELECTOR, "button.infinite-scroller__show-more-button")
            if see_more_btn.is_displayed():
                print("  -> Clicking 'See more jobs' button...")
                driver.execute_script("arguments[0].click();", see_more_btn)
                time.sleep(5)
        except:
            pass 
            
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("  -> Hit the bottom, waiting 10 extra seconds just in case...")
            time.sleep(10) #wait a bit longer at the bottom to ensure all jobs are loaded before we check the height again
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("  -> No more new jobs loading. Stopping scroll.")
                break
        last_height = new_height

    # timer to ensure all dynamic content is fully loaded before we start parsing the page source. This is important because sometimes even after scrolling, some jobs might still be loading in the background, and we want to make sure we capture everything.
    print("\nScrolling done! Waiting for 2 full minutes (120 seconds) to ensure everything is rendered...")
    time.sleep(120) 

    print("Extracting data...")
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    job_cards = soup.find_all('div', class_='base-card')
    print(f"Found {len(job_cards)} job cards for {keyword}. Saving to database...")
    
    new_jobs_count = 0
    for card in job_cards:
        try:
            title_tag = card.find('h3', class_='base-search-card__title')
            link_tag = card.find('a', class_='base-card__full-link')
            
            if not title_tag or not link_tag:
                continue
                
            title = title_tag.text.strip()
            link = link_tag['href'].split('?')[0] 
            
            company_tag = card.find('h4', class_='base-search-card__subtitle')
            company = company_tag.text.strip() if company_tag else "Unknown"
            description = f"Company: {company}"
            
            exists = session.query(RawJob).filter_by(job_link=link).first()
            if not exists:
                new_job = RawJob(platform="LinkedIn", job_title=title, job_link=link, description=description, published_date=datetime.now())
                session.add(new_job)
                new_jobs_count += 1
                
        except Exception as e:
            continue
            
    session.commit()
    driver.quit()
    print(f"Success! Added {new_jobs_count} NEW jobs for {keyword}.")
    
if __name__ == "__main__":
    # most in-demand tech job titles and keywords to search for on LinkedIn (you can customize this list based on your target audience or specific tech categories you want to focus on)
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
        "UI UX Designer"
    ]
    
    for kw in tech_keywords:
        scrape_linkedin_jobs(kw, "Egypt")