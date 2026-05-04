# CVision - Data Science Pipeline & Core API 

CVision is an AI-powered intelligent job-matching platform designed to bridge the gap between job seekers' resumes and real-time market opportunities. 

This repository houses the **Data Engineering Engine** of the project: the automated data collection, storage, NLP-cleaning pipeline, and the REST API that feeds the AI Agents.

---

## System Architecture & Project Roadmap

The CVision ecosystem is divided into two main layers. **This repository covers Layer 1.**

### Layer 1: Data Infrastructure (Current Repository)
* **Data Ingestion:** Automated Python scrapers (Selenium & REST APIs) gathering live tech jobs from LinkedIn and Remotive.
* **Historical Data Integration:** Consolidation of 6,400+ historical freelance jobs (Upwork, Freelancer, Guru) for AI model training.
* **Cloud Database:** Centralized storage using **Neon (PostgreSQL)**.
* **NLP Data Cleaning:** A preprocessing pipeline that removes HTML tags, URLs, and formatting noise to prepare text for Vector Embeddings.
* **Core API:** A **FastAPI** bridge serving clean, structured JSON data to the AI orchestrator.

### Layer 2: AI Orchestration & Frontend (Next Steps for the Team)
* **LangGraph Orchestrator:** Managing the flow of AI Agents.
    * *Agent 1 (CV Reader):* Extracts text from uploaded PDF/Word resumes.
    * *Agent 2 (CV Analyzer):* Uses LLMs (Gemini / Groq) to extract user skills.
    * *Agent 3 (Job Matcher):* Consumes data from **our FastAPI**, generates Vector Embeddings, calculates Match Scores (Cosine Similarity), and identifies Skill Gaps.
    * *Agent 4 (Report Builder):* Generates the final user report.
* **Frontend:** A React/Vercel web interface for user interaction.

---

## Repository Structure

```text
CVision/
│
├── Data/                       # Historical training datasets (Excel/JSON)
├── scrapers/                   # Automated scraping scripts
│   ├── jobs_scraper.py         # Remotive API global tech jobs scraper
│   ├── linkedin_scraper.py     # Advanced LinkedIn scraper with pagination bypass
│
├── api.py                      # FastAPI server for data serving
├── cvision.ipynb               # Jupyter notebook for AI & Data exploration
├── data_cleaner.py             # Text cleaning pipeline (HTML, URLs, formatting)
├── db_setup.py                 # SQLAlchemy Database schema & table initialization
├── training_data.py            # Script to merge and upload historical data
├── run_scraper.bat             # Windows Batch file for Task Scheduler automation
├── .env                        # Environment variables (Database connection secrets)
└── requirements.txt            # Python dependencies

    Setup & Installation
1. Clone the repository & activate the virtual environment:

Bash

git clone [https://github.com/yourusername/CVision.git](https://github.com/yourusername/CVision.git)
cd CVision
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On Mac/Linux
source .venv/bin/activate

2. Install dependencies:

Bash

pip install -r requirements.txt
3. Configure Environment Variables:
Create a .env file in the root directory and add your PostgreSQL database URL:

Ini, TOML

DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require

