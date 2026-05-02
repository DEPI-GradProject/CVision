# linkedin_scraper.py
import time
import os
from datetime import datetime
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
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
    
    # السطر ده هو السر: هنا بندي للسيلينيوم مسار متصفح Brave على جهازك
    chrome_options.binary_location = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    
    # chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-notifications")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# --- 3. Scraping Logic ---
def scrape_linkedin_jobs(keyword, location="Egypt"):
    print(f"Starting LinkedIn Scraper for: {keyword} in {location}...")
    driver = setup_driver()
    
    # تظبيط اللينك عشان يبحث في الوظايف العامة
    search_url = f"https://www.linkedin.com/jobs/search?keywords={keyword.replace(' ', '%20')}&location={location.replace(' ', '%20')}"
    driver.get(search_url)
    
    # بنعمل Scroll لتحت عشان نحمل وظايف أكتر
    print("Scrolling to load more jobs...")
    scroll_pause_time = 2
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    for _ in range(5): # هينزل 5 مرات، تقدر تزودهم عشان تجيب وظايف أكتر
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    print("Extracting data...")
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # استخراج كروت الوظايف
    job_cards = soup.find_all('div', class_='base-card')
    print(f"Found {len(job_cards)} job cards. Saving to database...")
    
    new_jobs_count = 0
    
    for card in job_cards:
        try:
            # استخراج عنوان الوظيفة واللينك
            title_tag = card.find('h3', class_='base-search-card__title')
            link_tag = card.find('a', class_='base-card__full-link')
            
            if not title_tag or not link_tag:
                continue
                
            title = title_tag.text.strip()
            link = link_tag['href'].split('?')[0] # بنشيل الزيادات من اللينك
            
            # استخراج اسم الشركة
            company_tag = card.find('h4', class_='base-search-card__subtitle')
            company = company_tag.text.strip() if company_tag else "Unknown"
            
            # هنحط اسم الشركة مع الوصف مؤقتاً لحد ما نعملها عمود لوحدها لو حبيت
            description = f"Company: {company}"
            
            # التأكد إنها مش متكررة
            exists = session.query(RawJob).filter_by(job_link=link).first()
            if not exists:
                new_job = RawJob(
                    platform="LinkedIn",
                    job_title=title,
                    job_link=link,
                    description=description,
                    published_date=datetime.now()
                )
                session.add(new_job)
                new_jobs_count += 1
                
        except Exception as e:
            continue
            
    session.commit()
    driver.quit()
    print(f"\nSuccess! Added {new_jobs_count} NEW jobs to the database from LinkedIn.")

if __name__ == "__main__":
    # تقدر تغير الكلمة والمكان زي ما تحب
    scrape_linkedin_jobs("Software Engineer", "Egypt")
    scrape_linkedin_jobs("Data Scientist", "Egypt")