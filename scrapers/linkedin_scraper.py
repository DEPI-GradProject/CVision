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
    
    # عشان نخفف الحمل على جهازك وهو بيسحب
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
    
    # هنخليه ينزل براحته 25 مرة
    for i in range(25): 
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print(f"  -> Scroll {i+1}/25... waiting 5 seconds for jobs to load")
        time.sleep(5) # وقت أطول للتحميل بين كل سكرول
        
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
            time.sleep(10) # لو وصل للآخر يصبر 10 ثواني يمكن حاجة بتحمل
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("  -> No more new jobs loading. Stopping scroll.")
                break
        last_height = new_height

    # التايمر اللي إنت طلبته (دقيقتين = 120 ثانية) قبل ما يستخرج الداتا ويقفل
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
    # قائمة بكل المجالات المشهورة (تقدر تضيف أو تمسح منها براحتك)
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