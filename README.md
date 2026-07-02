# CVision — AI-Powered Career Intelligence Platform

CVision is an end-to-end AI platform that analyzes CVs/resumes, extracts skills, computes ATS (Applicant Tracking System) scores, matches candidates against live job postings, and generates detailed reports. Built with a **LangGraph** multi-agent orchestration pipeline, a **FastAPI** backend, and a **React/TypeScript** frontend.

## Architecture — 4 LangGraph Agents

The CV processing pipeline is a directed acyclic graph (DAG) of 4 specialized AI agents, each responsible for one stage:

```
Upload → cv_parser → cv_analyzer → job_matcher → report_builder → Results
```

| Agent | File | Responsibility |
|---|---|---|
| **CV Parser** | `agents/cv_parser.py` | Extracts raw text from uploaded PDF/DOCX files using `pdfplumber` / `python-docx` |
| **CV Analyzer** | `agents/cv_analyzer.py` | Uses Groq (llama-3.3-70b) via LangChain to extract structured skills, experience, education, and compute an ATS score |
| **Job Matcher** | `agents/job_matcher.py` | Queries the job database, generates embeddings with `bge-small-en-v1.5`, finds top matches via cosine similarity on a FAISS vector index |
| **Report Builder** | `agents/report_builder.py` | Aggregates parser, analyzer, and matcher outputs into a human-readable final report with skill-gap analysis |

The graph runs synchronously for direct responses or as an SSE stream for real-time progress updates.

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11, FastAPI, Uvicorn |
| **AI Orchestration** | LangGraph, LangChain |
| **LLM** | Groq (llama-3.3-70b-versatile) |
| **Embeddings / Vector Search** | sentence-transformers (bge-small-en-v1.5), FAISS |
| **Database** | PostgreSQL (Neon), SQLAlchemy 2.0, Alembic |
| **Auth** | fastapi-users v15 (JWT, bcrypt password hashing) |
| **Rate Limiting** | slowapi (60 req/min default, 5 req/min on CV analysis) |
| **Monitoring** | Sentry |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS v4, Framer Motion |
| **Containerization** | Docker, docker-compose |
| **CI/CD** | GitHub Actions (ruff lint + pytest + docker build) |

## API Endpoints

### Auth (public)

| Method | Path | Description | Auth |
|---|---|---|---|
| POST | `/auth/register` | Create a new user account (email + password) | ❌ |
| POST | `/auth/login` | Log in, receive a JWT access token (form-data: username=email, password) | ❌ |
| POST | `/auth/logout` | Log out the current session | ✅ |
| GET | `/auth/me` | Get the authenticated user's profile | ✅ |
| PATCH | `/auth/me` | Update the authenticated user's profile | ✅ |

### Data (public)

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/api/v1/health` | Health check with database connectivity status | ❌ |
| GET | `/api/v1/jobs/latest` | Fetch the most recently scraped live jobs (default limit: 50) | ❌ |
| GET | `/api/v1/jobs/training` | Fetch historical cleaned training jobs (default limit: 100) | ❌ |

### CV Analysis (authenticated)

| Method | Path | Description | Auth |
|---|---|---|---|
| POST | `/api/v1/analyze-cv` | Upload a PDF/DOCX CV for full analysis (returns JSON with ATS score, skills, job matches, report) | ✅ |
| POST | `/api/v1/analyze-cv/stream` | Upload a CV for streaming analysis (returns Server-Sent Events with per-step progress) | ✅ |

Auth is handled via **Bearer JWT** token. Include `Authorization: Bearer <token>` in request headers.

## Frontend Pages

| Page | Route | Description |
|---|---|---|
| **Home** | `/` | Landing page with hero section, feature cards, and calls-to-action |
| **Upload CV** | `/upload` | Drag-and-drop / file-picker for CV upload (PDF/DOCX, max 10MB) |
| **Analysis** | `/analysis` | Real-time SSE progress display (parsing → scoring → matching → report) with ATS gauge, skill cloud, and full report |
| **Dashboard** | `/dashboard` | Aggregate statistics (CVs analyzed, avg score, jobs matched) and searchable history |
| **Login** | `/login` | Sign-in form with email/password, validation, error toast |
| **Register** | `/register` | Create account form with email/password/confirm, auto-login on success |

## Setup & Installation

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL database (local or Neon/cloud)

### 1. Clone and configure

```bash
git clone https://github.com/yourusername/CVision.git
cd CVision
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac / Linux
source .venv/bin/activate
```

### 2. Environment variables

```bash
cp .env.example .env
```

Fill in all 14 variables in `.env`:

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | ✅ | PostgreSQL connection string (`postgresql://user:password@host:5432/dbname?sslmode=require`) |
| `GROQ_API_KEY` | ✅ | Groq API key for LLM inference |
| `GOOGLE_API_KEY` | ❌ | Google AI / Gemini API key (optional) |
| `OPENAI_API_KEY` | ❌ | OpenAI API key (optional fallback) |
| `TAVILY_API_KEY` | ❌ | Tavily search API key (optional) |
| `SENTRY_DSN` | ❌ | Sentry DSN for error monitoring (optional) |
| `AUTH_JWT_SECRET` | ✅ | Random secret string for JWT signing |
| `AUTH_JWT_LIFETIME_SECONDS` | ❌ | JWT token lifetime in seconds (default: 3600) |
| `FAISS_ALLOW_DANGEROUS` | ❌ | Set to `true` to allow loading unsigned FAISS index |
| `CHROME_BROWSER_PATH` | ❌ | Path to Chrome/Brave binary (for LinkedIn scraper) |
| `LINKEDIN_LOCATION` | ❌ | Location filter for LinkedIn scraping |
| `SCROLL_PAUSE_SECONDS` | ❌ | Pause between scrolls (LinkedIn scraper) |
| `MAX_SCROLLS` | ❌ | Max scroll iterations (LinkedIn scraper) |
| `FINAL_WAIT_SECONDS` | ❌ | Final wait time (LinkedIn scraper) |

### 3. Backend

```bash
pip install -r requirements.txt
alembic upgrade head
python utils/ingest.py           # Build FAISS vector index from training data
uvicorn api:app --reload
```

API docs available at `http://localhost:8000/docs`.

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173` with hot-reload and proxies `/api` and `/auth` requests to the backend.

### 5. Run tests

```bash
pytest tests/
```

## Docker

```bash
docker-compose up --build
```

This builds the API container and runs it on port 8000.

## Project Structure

```
CVision/
├── agents/                  # LangGraph AI agent implementations
│   ├── cv_parser.py
│   ├── cv_analyzer.py
│   ├── job_matcher.py
│   └── report_builder.py
├── auth/                    # Authentication module (fastapi-users)
│   ├── __init__.py          # FastAPIUsers setup, JWT backend, dependencies
│   ├── database.py          # Async SQLAlchemy engine (lazy init)
│   ├── db.py                # get_user_db dependency
│   └── auth_user_manager.py # UserManager hooks
├── graph/                   # LangGraph workflow definition
│   └── workflow.py          # StateGraph with 4 nodes + conditional edges
├── models/                  # Pydantic schemas + SQLAlchemy models
│   ├── schemas.py           # AgentState, AnalysisResult, etc.
│   └── db_models.py         # User, Base (DeclarativeBase)
├── scrapers/                # Job data scrapers
│   ├── linkedin_scraper.py
│   └── jobs_scraper.py
├── utils/                   # Utilities
│   ├── file_handler.py
│   ├── ingest.py            # FAISS index builder
│   └── retriever.py         # Vector search retriever
├── alembic/                 # Database migrations
│   └── versions/
├── tests/                   # Pytest tests
│   ├── test_agents.py
│   ├── test_api.py
│   ├── test_file_handler.py
│   └── test_schemas.py
├── frontend/                # React + TypeScript + Vite frontend
│   └── src/
│       ├── pages/           # 6 pages (Home, Upload, Analysis, Dashboard, Login, Register)
│       ├── components/      # Reusable UI components
│       ├── contexts/        # AuthContext (JWT in memory)
│       └── api/             # client.ts (HTTP client with auth headers)
├── api.py                   # FastAPI app, routes, middleware
├── config.py                # Pydantic Settings
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── requirements.txt
└── pyproject.toml
```
