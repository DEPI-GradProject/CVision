# CVision — AI-Powered Career Intelligence Platform

[![CI](https://github.com/DEPI-GradProject/CVision/actions/workflows/ci.yml/badge.svg)](https://github.com/DEPI-GradProject/CVision/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-311/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

CVision analyzes CVs/resumes, extracts skills, computes ATS scores, matches candidates against live job postings, and generates detailed reports. Built with a **LangGraph** multi-agent pipeline, **FastAPI** backend, and **React/TypeScript** frontend.

## Architecture — 4 LangGraph Agents

```
Upload → cv_parser → cv_analyzer → job_matcher → report_builder → Results
```

| Agent | File | Responsibility |
|---|---|---|
| **CV Parser** | `agents/cv_parser.py` | Extracts text from PDF/DOCX |
| **CV Analyzer** | `agents/cv_analyzer.py` | Extracts skills, experience, ATS score via Groq |
| **Job Matcher** | `agents/job_matcher.py` | FAISS vector search for top job matches |
| **Report Builder** | `agents/report_builder.py` | Aggregates all outputs into final report |

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11, FastAPI, Uvicorn |
| **AI** | LangGraph, LangChain, Groq (llama-4 / llama-3.1) |
| **Vector Search** | sentence-transformers (bge-small-en-v1.5), FAISS |
| **Database** | PostgreSQL / SQLite, SQLAlchemy 2.0, Alembic |
| **Auth** | fastapi-users v15 (JWT, bcrypt) |
| **Rate Limiting** | slowapi (60/min default, 10/min auth, 5/min CV analysis) |
| **Monitoring** | Sentry |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS v4 |
| **CI/CD** | GitHub Actions (lint, pre-commit, pytest, pip-audit, mypy, docker build, Trivy) |

## API Endpoints

### Auth
| Method | Path | Auth |
|---|---|---|
| POST | `/auth/register` | ❌ |
| POST | `/auth/login` | ❌ |
| POST | `/auth/logout` | ✅ |
| GET | `/auth/me` | ✅ |
| PATCH | `/auth/me` | ✅ |

### Data
| Method | Path | Auth |
|---|---|---|
| GET | `/api/v1/health` | ❌ |
| GET | `/api/v1/jobs/latest` | ❌ |
| GET | `/api/v1/jobs/training` | ❌ |

### CV Analysis
| Method | Path | Auth |
|---|---|---|
| POST | `/api/v1/analyze-cv` | ✅ |
| POST | `/api/v1/analyze-cv/stream` | ✅ (SSE) |
| POST | `/api/v1/match-job` | ✅ |
| POST | `/api/v1/match-job/file` | ✅ |
| POST | `/api/v1/tailor-resume` | ✅ |
| POST | `/api/v1/stand-out` | ✅ |
| POST | `/api/v1/cover-letter` | ✅ |
| POST | `/api/v1/rewrite-suggestions` | ✅ |
| GET | `/api/v1/history` | ✅ |
| GET | `/api/v1/stats` | ✅ |
| GET | `/api/v1/skills/market-demand` | ✅ |

Auth: **Bearer JWT** (`Authorization: Bearer <token>`).

## Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL (production) or SQLite (development)

### 1. Clone & create venv
```bash
git clone https://github.com/DEPI-GradProject/CVision.git
cd CVision
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
```

### 2. Environment variables
```bash
cp .env.example .env
```

Key variables:
| Variable | Required | Default |
|---|---|---|
| `DATABASE_URL` | ✅ | `sqlite:///./data/cvision.db` |
| `GROQ_API_KEY` | ✅ | — |
| `AUTH_JWT_SECRET` | ✅ | — |
| `AUTH_JWT_LIFETIME_SECONDS` | ❌ | 3600 |
| `FAISS_ALLOW_DANGEROUS` | ❌ | False |
| `CORS_ORIGINS` | ❌ | `*` |
| `SENTRY_DSN` | ❌ | (blank) |

### 3. Backend
```bash
pip install -e ".[test]"
alembic upgrade head
python utils/ingest.py              # build FAISS index
uvicorn api:app --reload
```

Docs: `http://localhost:8000/docs`

### 4. Frontend
```bash
cd frontend
npm install
npm run dev
```

### 5. Run tests
```bash
pytest tests/ --cov=api --cov=auth --cov=models --cov=utils --cov=agents --cov=graph
```

## Docker
```bash
# Development
docker compose up --build

# Production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Project Structure
```
CVision/
├── agents/                  # LangGraph AI agents
├── auth/                    # JWT auth (fastapi-users)
├── graph/                   # StateGraph workflow
├── models/                  # Pydantic + SQLAlchemy models
├── scrapers/                # Job data scrapers
├── utils/                   # File handler, FAISS ingest, retriever
├── alembic/                 # DB migrations
├── tests/                   # 70+ pytest tests
├── frontend/                # React + Vite SPA
├── api.py                   # FastAPI app
├── config.py                # Pydantic Settings
├── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
├── .github/workflows/       # CI/CD
└── pyproject.toml
```
