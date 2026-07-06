# CVision — AI-Powered CV Analysis Platform

## Project Explained for Graduation Defense

---

# 1. What the Project Does

CVision is a web application that helps job seekers improve their CVs and find matching jobs. A user uploads their CV (PDF or DOCX file), and the system runs it through four AI agents that parse the content, analyze it for ATS (Applicant Tracking System) compatibility, extract skills, match against a database of jobs, and generate a detailed career report.

The problem it solves: Most companies use ATS software to screen CVs before a human ever reads them. Studies show that 75% of qualified candidates are rejected by ATS systems because their CVs are not formatted correctly. CVision gives job seekers a clear picture of how their CV performs against ATS criteria, what skills they should highlight, and which job opportunities match their profile.

The user journey is simple:
1. A user opens the website and sees a landing page explaining the service.
2. They register an account (email + password) and log in.
3. They upload their CV (drag-and-drop or file picker).
4. They watch in real-time as four AI agents process their CV — parsing text, computing an ATS score, matching against jobs, and building a report.
5. They see their results: an ATS score (0-100), a list of extracted skills, number of matching jobs, and a full written career report.
6. They can view their analysis history on a dashboard.

The project is built for individual job seekers, career advisors, and university career centers. It is deployed as a modern single-page application with a REST API backend.

---

# 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React + Vite)                         │
│                                                                            │
│  Home · Register · Login · Upload · Analysis (SSE) · Dashboard            │
│  Tailwind CSS · Framer Motion · TypeScript                                 │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │  HTTP (JSON / SSE)
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI + Uvicorn)                         │
│                                                                            │
│  /api/v1/health · /auth/register · /auth/login · /auth/me                 │
│  /api/v1/analyze-cv · /api/v1/analyze-cv/stream (SSE)                     │
│  /api/v1/jobs/latest · /api/v1/jobs/training                              │
│  /api/v1/history · /api/v1/stats                                          │
│                                                                            │
│  Middleware: CORS · Rate Limiting (slowapi) · Sentry (optional)            │
└────────┬─────────────────────────────┬──────────────────┬───────────────┘
         │                             │                  │
         ▼                             ▼                  ▼
┌─────────────────┐    ┌─────────────────────────┐   ┌─────────────┐
│   PostgreSQL    │    │   AI Agent Pipeline     │   │  FAISS      │
│   (Neon)        │    │   (LangGraph)           │   │  Vector DB  │
│                 │    │                         │   │             │
│  users          │    │  cv_parser ──►          │   │  BGE Small  │
│  jobs_raw       │    │  cv_analyzer ──►        │   │  Embeddings │
│  training_jobs  │    │  job_matcher ──►        │   │             │
│  analysis_history│   │  report_builder ──► END │   │  jobs.csv   │
└─────────────────┘    └──────────┬──────────────┘   └─────────────┘
                                  │
                                  ▼
                       ┌─────────────────────┐
                       │  Groq Cloud (LLM)   │
                       │                     │
                       │  Llama 3.3-70B      │
                       │  Llama 3.1-8B       │
                       └─────────────────────┘
```

### Why Each Technology Was Chosen

**FastAPI over Flask/Django**: FastAPI is asynchronous by default, which is essential for handling file uploads and SSE streaming without blocking the server. It also generates automatic OpenAPI documentation and has built-in validation through Pydantic.

**React + Vite over Next.js/CRA**: Vite provides instant hot reloading and fast builds. React was chosen because of its ecosystem (react-router, framer-motion) and because the team has more experience with it. A full framework like Next.js was unnecessary since SEO is not critical for this application.

**PostgreSQL over SQLite/MongoDB**: The data is highly relational (users own analysis records, which reference jobs). PostgreSQL is the standard for production databases, and Neon provides a free hosted PostgreSQL with SSL support. The schema is well-defined and does not benefit from a document store.

**LangGraph over plain functions**: This is the most important architectural decision. The four agents must run in sequence, each depending on the output of the previous one. LangGraph provides:
- A state machine that enforces the execution order
- Built-in error handling — if one agent fails, the pipeline stops with a clear error
- Streaming support — the frontend receives real-time updates as each agent completes
- A clear, declarative graph structure that is easy to modify, test, and explain
- Without LangGraph, we would have to write manual if/else chains and state management, which is error-prone and harder to extend (e.g., adding a fifth agent or conditional branching).

**FAISS over SQL LIKE search**: SQL full-text search uses keyword matching (it looks for the exact words). FAISS performs semantic search — it converts text to vectors (embeddings) and finds jobs that are *conceptually* similar to the candidate's skills. For example, a SQL search for "Python" would miss a job asking for "Django" or "backend development", but FAISS would catch it because their vectors are close in the embedding space.

**Groq over OpenAI (cost/latency)**: Groq provides extremely fast inference on Llama models (up to 500 tokens/second) at a fraction of the cost of GPT-4. For this use case, Llama 3.3-70B is powerful enough for analysis and report generation, while Llama 3.1-8B is used for the simpler query enhancement step.

---

# 3. The AI Agent Pipeline

## Pipeline Flow Diagram

```
                         ┌──────────────┐
                         │    START     │
                         │  User upload │
                         │  CV (PDF/DOCX)│
                         └──────┬───────┘
                                │
                                ▼
                     ┌────────────────────┐
                     │                    │
                     │  1. cv_parser      │
                     │                    │
                     │  Input: file_path  │
                     │  + file_name       │
                     │                    │
                     │  - Extracts text   │
                     │  - Extracts PDF    │
                     │    metadata        │
                     │  - Detects sections│
                     │                    │
                     │  Output: cv_data   │
                     │  (raw_text +       │
                     │   CVMetadata)      │
                     │                    │
                     └────────┬───────────┘
                              │
                    ┌─────────▼──────────┐
                    │  Error? ──► END    │
                    └─────────┬──────────┘
                              │
                              ▼
                     ┌────────────────────┐
                     │                    │
                     │ 2. cv_analyzer     │
                     │                    │
                     │  Uses LLM (Groq):  │
                     │  - Calls ats_check │
                     │    tool for format │
                     │  - Analyzes skills │
                     │  - Lists strengths │
                     │    & weaknesses    │
                     │                    │
                     │  Output: analysis  │
                     │  (ATSResult +      │
                     │   AnalysisResult)  │
                     │                    │
                     └────────┬───────────┘
                              │
                    ┌─────────▼──────────┐
                    │  Error? ──► END    │
                    └─────────┬──────────┘
                              │
                              ▼
                     ┌────────────────────┐
                     │                    │
                     │ 3. job_matcher     │
                     │                    │
                     │  - Query enhance   │
                     │    (LLM small)     │
                     │  - FAISS search    │
                     │    (semantic)      │
                     │  - Match scoring   │
                     │    (LLM large)     │
                     │                    │
                     │  Output:           │
                     │  job_matches       │
                     │  (list of Job      │
                     │   with scores)     │
                     │                    │
                     └────────┬───────────┘
                              │
                    ┌─────────▼──────────┐
                    │  Error? ──► END    │
                    └─────────┬──────────┘
                              │
                              ▼
                     ┌────────────────────┐
                     │                    │
                     │ 4. report_builder  │
                     │                    │
                     │  - Aggregates all  │
                     │    previous output │
                     │  - LLM generates   │
                     │    a 6-section     │
                     │    career report   │
                     │                    │
                     │  Output:           │
                     │  final_report      │
                     │  (markdown text)   │
                     │                    │
                     └────────┬───────────┘
                              │
                              ▼
                         ┌──────────┐
                         │   END    │
                         │ Results  │
                         │ returned │
                         │ to user  │
                         └──────────┘
```

## Agent 1: `cv_parser`

**What it receives**: The raw file path and file name from the uploaded CV.

**What it does step by step**:
1. Detects the file type (PDF or DOCX).
2. For PDF: Uses PyMuPDF (fitz) to extract all text from every page. For DOCX: Uses python-docx to extract text from paragraphs and tables.
3. If the file is a PDF, it also extracts metadata:
   - Counts pages.
   - Checks for tables (using PyMuPDF's `find_tables()`).
   - Checks for embedded images (using `page.get_images()`).
   - Counts unique fonts used across the document.
   - Checks which of 13 predefined sections exist in the CV text (experience, education, skills, summary, objective, projects, certifications, languages, references, achievements, awards, volunteer, publications).
   - Determines which sections are missing.
4. Wraps everything into a `CVData` object containing raw_text, file_name, file_type, and optional metadata.

**What it produces**: A `CVData` object with the full text content and structural metadata.

**LLM calls**: None — this is a pure Python agent using PDF/document processing libraries.

## Agent 2: `cv_analyzer`

**What it receives**: The `CVData` from the parser (raw text + metadata).

**What it does step by step**:
1. Prepares a JSON payload with the metadata (has_tables, has_images, fonts_count, pages_count, sections_found, and cv_text).
2. Invokes the Groq LLM (Llama 3.3-70B, temperature 0.3) with a prompt that asks it to:
   - Call the built-in `ats_checker` tool to compute a rule-based ATS score.
   - Analyze the CV text and extract: strengths, weaknesses, suggestions for improvement, and skills found.
3. The `ats_checker` tool is a deterministic Python function (not an LLM call) that calculates scores in four categories:
   - **Format (25%)**: Deducts points for tables (-30), images (-20), too many fonts (-10 to -20).
   - **Structure (25%)**: Checks for required sections (experience, education, skills), dates, and summary/objective.
   - **Content (25%)**: Checks for action verbs (managed, developed, etc.), personal information (date of birth, nationality, etc.), and quantifiable achievements (numbers).
   - **Length (25%)**: Penalizes CVs shorter than 1 page or longer than 2 pages.
4. After the LLM responds, the agent parses the JSON from the LLM response (handling markdown code blocks with ```json).
5. Constructs an `AnalysisResult` object.

**What it produces**: An `AnalysisResult` containing strengths list, weaknesses list, suggestions list, skills_extracted list, and an `ATSResult` with score, breakdown, and issues.

**LLM calls**: 1 call to Llama 3.3-70B (the LLM internally calls the `ats_checker` tool).

## Agent 3: `job_matcher`

**What it receives**: The `AnalysisResult` from the analyzer (specifically, the extracted skills list).

**What it does step by step**:
1. Takes the comma-separated list of extracted skills.
2. **Query Enhancement**: Sends the skills to a smaller, faster LLM (Llama 3.1-8B, temperature 0.1) to generate an expanded search query. For example, if the skills are "Python, FastAPI, Docker", it might produce "Python backend developer FastAPI Docker microservices API".
3. **Semantic Search**: Takes the enhanced query and searches the FAISS vector database for the top 10 most relevant jobs (using cosine similarity on BGE embeddings).
4. **Match Scoring**: Sends the candidate's skills and the raw job results to a larger LLM (Llama 3.3-70B, temperature 0.1) that scores each job on a 0-100 scale, identifies matched and missing skills, and writes a reason for each match.
5. Parses the LLM JSON output.
6. Constructs a `JobMatches` object with a list of `Job` objects (each with title, link, skills, match_score, matched_skills, missing_skills, reason).

**What it produces**: A `JobMatches` object containing an ordered list of matching jobs with detailed scoring.

**LLM calls**: 2 calls — 1 small LLM for query enhancement, 1 large LLM for match scoring.

## Agent 4: `report_builder`

**What it receives**: The `AnalysisResult` and `JobMatches` from the previous two agents.

**What it does step by step**:
1. Aggregates all data: strengths, weaknesses, suggestions, skills, ATS score with breakdown, ATS issues, and matched jobs with their details.
2. Sends everything to the Groq LLM (Llama 3.3-70B, temperature 0.3) with a structured prompt that asks for a professional career report with six sections:
   - Executive Summary
   - Strengths
   - Areas for Improvement
   - ATS Optimization Tips
   - Top Job Matches (with match score interpretation)
   - Action Plan (3-5 concrete steps)
3. The LLM generates a comprehensive paragraph-style report.

**What it produces**: A `final_report` string (markdown-formatted career report).

**LLM calls**: 1 call to Llama 3.3-70B.

**Total LLM calls per analysis**: Up to 4 (1 for analyzer, 2 for matcher, 1 for report).

---

# 4. Authentication System

## What is JWT?

JWT stands for JSON Web Token. It is a small, self-contained piece of data that proves a user's identity. Think of it like a digital ID card:

- When you log in, the server gives you a JWT.
- The JWT contains encoded information (user ID, expiration time).
- The server signs the JWT with a secret key, so it cannot be forged.
- The client sends this JWT with every request in the HTTP `Authorization` header.
- The server can verify the JWT without querying the database, because the signature proves it was issued by the server.

JWT eliminates the need for the client to send a password with every request. It also enables stateless authentication — the server does not need to store session data.

## Step-by-Step Flow

### Registration
1. User fills in email + password on the Register page.
2. Frontend sends `POST /auth/register` with `{"email": "...", "password": "..."}`.
3. FastAPI (using fastapi-users) receives the request:
   - Validates the email format (using Pydantic's `EmailStr`).
   - Hashes the password using bcrypt (done internally by fastapi-users).
   - Stores the user record in the `users` table with fields: id, email, hashed_password, is_active, is_superuser, is_verified.
   - Returns the user object (id, email, is_active, is_superuser, is_verified).
4. The frontend auto-logs in the user by calling login immediately after successful registration.

### Login
1. User fills in email + password on the Login page.
2. Frontend sends `POST /auth/login` with form-encoded data (username=email, password=...).
3. FastAPI verifies:
   - The user exists in the database.
   - The password hash matches using bcrypt.
4. If valid, the server creates a JWT containing:
   - `sub` (subject): the user's ID
   - `exp` (expiration): current time + 3600 seconds (1 hour)
   - The token is signed with `AUTH_JWT_SECRET` using the HS256 algorithm.
5. The server returns `{"access_token": "<jwt>", "token_type": "bearer"}`.
6. The frontend stores the token in memory and sends it as `Authorization: Bearer <token>` on all subsequent requests.

### Protected Request (e.g., analyzing a CV)
1. Frontend sends `POST /api/v1/analyze-cv` with `Authorization: Bearer <token>`.
2. FastAPI extracts the JWT from the header.
3. The `current_active_user` dependency:
   - Verifies the JWT signature using the same `AUTH_JWT_SECRET`.
   - Checks the expiration time — if expired, returns 401.
   - Extracts the user ID from the `sub` field.
   - Loads the user from the database (to verify the account is still active).
   - Returns the user object to the route handler.
4. If the token is missing, expired, or invalid, the server returns 401 Unauthorized.

### Logout
1. Frontend sends `POST /auth/logout`.
2. Since JWTs are stateless, the server simply acknowledges the logout.
3. The frontend discards the token from memory.
4. If someone tries to reuse the old token, it will eventually expire (after 1 hour).

## Security Notes
- Passwords are never stored in plain text. fastapi-users uses bcrypt (via passlib) to hash passwords before storage.
- The JWT secret is stored in the `.env` file and never exposed to the client.
- The JWT has a 1-hour expiration to limit the damage if a token is leaked.

---

# 5. Database Schema

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                           users                                 │
├─────────────────────────────────────────────────────────────────┤
│  id              INTEGER  PRIMARY KEY AUTOINCREMENT              │
│  email           VARCHAR(320)  NOT NULL  UNIQUE  INDEXED         │
│  hashed_password VARCHAR(1024) NOT NULL                           │
│  is_active       BOOLEAN  DEFAULT true                            │
│  is_superuser    BOOLEAN  DEFAULT false                           │
│  is_verified     BOOLEAN  DEFAULT false                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │  1
                            │
                            │  N  (foreign key: user_id)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     analysis_history                             │
├─────────────────────────────────────────────────────────────────┤
│  id              INTEGER  PRIMARY KEY AUTOINCREMENT               │
│  user_id         INTEGER  NOT NULL  INDEXED  → users.id          │
│  filename        VARCHAR(255) NOT NULL                            │
│  ats_score       INTEGER  nullable                                │
│  skills_extracted TEXT  nullable  (JSON string)                    │
│  job_matches     INTEGER  nullable                                │
│  created_at      DATETIME  NOT NULL                               │
│                                                                   │
│  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                          jobs_raw                                │
├─────────────────────────────────────────────────────────────────┤
│  id              INTEGER  PRIMARY KEY AUTOINCREMENT               │
│  platform        VARCHAR(50)  NOT NULL                            │
│  job_title       VARCHAR(255) NOT NULL                            │
│  job_link        VARCHAR  UNIQUE  NOT NULL                        │
│  description     TEXT  nullable                                   │
│  published_date  DATETIME  nullable                               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        training_jobs                             │
├─────────────────────────────────────────────────────────────────┤
│  id              INTEGER  PRIMARY KEY AUTOINCREMENT               │
│  Title           VARCHAR(255) NOT NULL                            │
│  Link            VARCHAR  nullable                                │
│  Skills          TEXT  nullable                                   │
│  Price           VARCHAR(50)  nullable                            │
│  Description     TEXT  nullable                                   │
│  platform_source VARCHAR(50)  nullable                            │
└─────────────────────────────────────────────────────────────────┘
```

## Table Details

### `users`
Stores registered user accounts. This table is managed by fastapi-users. The `SQLAlchemyBaseUserTable` mixin provides the standard columns. The `id` column uses Integer primary key (configured via `IntegerIDMixin`). The `email` column has a unique index for fast lookups during login. The `is_active` flag allows administrators to deactivate accounts without deleting them.

### `analysis_history`
Records every CV analysis performed by a user. The `user_id` column is a foreign key to `users.id` with `ON DELETE CASCADE` — if a user is deleted, their analysis history is automatically removed. The `skills_extracted` column is a TEXT field storing a JSON array (e.g., `["Python", "FastAPI"]`). It is stored as a string and parsed with `json.loads()` when read. The `created_at` timestamp enables sorting by most recent analysis (descending order).

### `jobs_raw`
Stores raw job listings scraped from external platforms (e.g., LinkedIn, Indeed). The `platform` field tracks the source. The `job_link` has a unique constraint to prevent duplicate entries. The `published_date` helps the frontend show the most recent jobs first.

### `training_jobs`
Stores a curated set of job listings used for training data and the FAISS vector search index. This table contains the data that was loaded into FAISS for semantic job matching. The `Skills` column is used as part of the job document content for embedding.

## Relationships
- **users 1:N analysis_history** — One user can have many analysis records.
- **analysis_history → users** — Each analysis belongs to exactly one user.
- **jobs_raw and training_jobs** are standalone tables with no foreign keys to users (they are reference data, not user-owned).

---

# 6. Vector Search / FAISS Explanation

## What are Embeddings?

Embeddings are a way to convert text into numbers that capture meaning.

Imagine you have two sentences:
- "I love Python programming"
- "I enjoy coding in Python"

A keyword search would fail to match these because they use different words. But an embedding converts each sentence into a vector (a list of ~384 numbers for the BGE model used here). The vectors for these two sentences will be very close together in the 384-dimensional space because they mean similar things. Vectors for unrelated sentences ("I love Python" vs "The sky is blue") will be far apart.

Our system uses the `BAAI/bge-small-en-v1.5` model from HuggingFace, which produces 384-dimensional vectors. This is a "small" model — it runs on CPU, takes about 100MB of RAM, and can embed a job description in under 100ms.

## How Job Matching Works

### Step 1: Ingestion (done once, before any user uses the system)

1. A CSV file (`Data/jobs.csv`) contains job listings with Title, Link, Skills, Price fields.
2. The `utils/ingest.py` script reads each row and creates a document: `"Title: {title}\nSkills: {skills}"`.
3. Each document is converted into a 384-dimensional vector using the BGE embedding model.
4. All vectors are stored in a FAISS index on disk (`Data/faiss_db/`).
5. An integrity hash (SHA-256) of the index files is saved to detect tampering.

### Step 2: Query Enhancement (during analysis)

When a user's CV is analyzed, the extracted skills (e.g., "Python, FastAPI, Docker, PostgreSQL") are sent to a fast LLM (Llama 3.1-8B) with a prompt that says: "Convert these skills into a rich semantic search query for finding relevant jobs." The LLM returns something like: "Python backend developer FastAPI Docker PostgreSQL REST API microservices."

This step is important because the raw skill list ("Python, FastAPI, Docker") is too sparse for good semantic search. The enhanced query adds context and related terms.

### Step 3: FAISS Similarity Search

1. The enhanced query is converted to a vector using the same BGE embedding model.
2. FAISS searches its index for the 10 vectors that are closest to the query vector (using cosine similarity / inner product).
3. FAISS returns the documents (job listings) associated with those nearest vectors.
4. This is extremely fast — searching 100,000 vectors takes under 10ms on a CPU.

### Step 4: LLM Re-Scoring

The raw FAISS results contain jobs that are semantically similar but may not be good matches for the specific candidate (e.g., a senior role vs junior, or missing critical skills). So the results are passed to a strong LLM (Llama 3.3-70B) that:
- Scores each job 0-100 based on how well the candidate's skills match.
- Identifies which skills match and which are missing.
- Writes a human-readable explanation for each match.

This two-stage approach (FAISS for speed + LLM for accuracy) combines the best of both: FAISS narrows the search from thousands of jobs to 10 in milliseconds, and the LLM provides intelligent scoring that understands context (e.g., "Python is required" vs "Python is preferred").

### Why FAISS Instead of SQL Search

| Capability | SQL LIKE / Full-Text Search | FAISS Vector Search |
|---|---|---|
| Match "Python developer" to "Backend engineer (Django)" | No — no common keywords | Yes — semantically similar |
| Handle typos ("Pythn") | No | Partially — similar vectors |
| Speed on 100k records | Fast (indexed) | Very fast (under 10ms) |
| Need for GPU/vector hardware | No | No (BGE-small runs on CPU) |
| Memory usage | Minimal | ~150MB for 100k jobs |
| Match without exact keywords | No | Yes |

The key advantage is semantic matching: a SQL query for "Python" will never return a job that says "Django experience required" unless it also mentions Python. FAISS will match them because the word "Django" appears in similar contexts to "Python" in the embedding model.

---

# 7. API Endpoints Reference

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/` | Health check — returns `{"message": "CVision API is Online"}` | No |
| GET | `/api/v1/health` | Database connectivity check — returns `{"status": "healthy", "database": "connected"}` | No |
| POST | `/auth/register` | Register a new user with email + password | No |
| POST | `/auth/login` | Login with email + password, returns JWT token | No |
| POST | `/auth/logout` | Logout (stateless — just acknowledges) | Yes |
| GET | `/auth/me` | Get current authenticated user's profile | Yes |
| PUT | `/auth/me` | Update current user's profile | Yes |
| DELETE | `/auth/me` | Delete current user's account | Yes |
| GET | `/auth/users/{id}` | Get a specific user by ID (admin) | Yes |
| PUT | `/auth/users/{id}` | Update a specific user (admin) | Yes |
| DELETE | `/auth/users/{id}` | Delete a specific user (admin) | Yes |
| POST | `/api/v1/analyze-cv` | Upload CV (PDF/DOCX) for full analysis | Yes |
| POST | `/api/v1/analyze-cv/stream` | Upload CV with Server-Sent Events (real-time progress) | Yes |
| POST | `/api/v1/analyze-cv/match-job` | Match CV against a specific job at time of analysis | Yes |
| GET | `/api/v1/jobs/latest` | Get latest scraped jobs (paginated, max 50) | No |
| GET | `/api/v1/jobs/training` | Get training job data (paginated, max 100) | No |
| POST | `/api/v1/jobs/match-job` | Match an already-analyzed CV against jobs or a specific job ID | Yes |
| POST | `/api/v1/jobs/match-job/file` | Upload CV + optional job ID, runs match independently | Yes |
| POST | `/api/v1/jobs/tailor-resume` | Tailor a CV resume section to match a specific job | Yes |
| POST | `/api/v1/jobs/stand-out` | Generate "stand-out" suggestions for a specific role/industry | Yes |
| POST | `/api/v1/jobs/cover-letter` | Generate a tailored cover letter for a CV + job pairing | Yes |
| POST | `/api/v1/skills/rewrite-suggestions` | Suggest specific rewrite improvements for CV bullet points | Yes |
| POST | `/api/v1/skills/market-demand` | Analyze skills market demand against a job description | Yes |
| GET | `/api/v1/history` | Get authenticated user's analysis history | Yes |
| GET | `/api/v1/stats` | Get authenticated user's aggregate statistics | Yes |

### Rate Limiting
- Default global limit: 60 requests per minute per IP.
- Health endpoint: 30 requests per minute.
- CV analysis endpoints (non-stream + stream): 5 requests per minute per user.

---

# 8. Frontend Pages

## Home Page (`/`)
- Landing page with animated hero section.
- Highlights four key features: Smart Parsing, ATS Scoring, Job Matching, Insights.
- Three-step guide: Upload CV → AI Analysis → Get Results.
- Calls: none (static page).
- Links to Upload and Dashboard pages.

## Register Page (`/register`)
- Registration form: email + password fields.
- On submit, calls `POST /auth/register`.
- On success, auto-calls `POST /auth/login` then `GET /auth/me` to set the session.
- React Router redirect to Upload page after successful registration.

## Login Page (`/login`)
- Login form: email + password fields.
- On submit, calls `POST /auth/login`.
- On success, calls `GET /auth/me` to get user profile.
- Redirects to Upload page.

## Upload Page (`/upload`)
- Drag-and-drop file picker for PDF/DOCX (max 10MB).
- Client-side validation of file type and size.
- On submit, navigates to Analysis page with the File object passed via React Router state.

## Analysis Page (`/analysis`)
- Connects to `/api/v1/analyze-cv/stream` using Server-Sent Events.
- Shows real-time step indicators: Parsing → Analyzing → Calculating ATS → Matching Jobs → Building Report.
- On completion, displays:
  - Animated ATS score gauge (circular progress).
  - Skills cloud (extracted skills as badges).
  - Number of job matches.
  - Full career report (markdown).
- If streaming fails, shows error state with "Try Again" button.

## Dashboard Page (`/dashboard`)
- Protected page — redirects to Login if not authenticated.
- Shows aggregate stats cards: CVs Analyzed, Average Score, Jobs Matched, Last Analysis.
- Shows analysis history as a searchable, scrollable list.
- Each history item shows: filename, date, extracted skills, ATS score.
- Calls `GET /api/v1/history` and `GET /api/v1/stats` on mount.

## Job Match Page (`/job-match`)
- Protected page — redirects to Login if not authenticated.
- User selects a previous analysis from a dropdown.
- Four action buttons: Find Jobs, Tailor Resume, Stand Out, Cover Letter.
- Each action calls the corresponding API endpoint and renders results in a right-side panel.
- Results panel supports markdown rendering for tailor/cover letter outputs.

## Protected Route Pattern
- All protected pages (`/analysis`, `/dashboard`, `/job-match`) use a `ProtectedRoute` wrapper component.
- `ProtectedRoute` checks `auth.isAuthenticated`; if false, redirects to `/login` with the intended destination in state.
- After login, the user is redirected back to the original page (not a hard-coded `/upload`).

---

# 9. Anticipated Professor Questions with Answers

### Q1: "Why did you choose LangGraph over just writing sequential functions?"

LangGraph provides four concrete benefits that simple functions do not:

1. **Guaranteed state machine**: Each agent receives the full `AgentState` and returns a modified copy. This prevents the common bug where a function modifies global state or forgets to pass a value. The graph enforces that `cv_parser` runs before `cv_analyzer`, which runs before `job_matcher`, which runs before `report_builder`.

2. **Conditional branching**: The `should_continue` function checks if `state.error` is set. If any agent fails, the pipeline stops immediately instead of continuing with corrupted data. With plain functions, we would need `if` checks between every function call.

3. **Built-in streaming**: LangGraph supports `graph.stream(state)` which yields the output of each node as it completes. The frontend uses this to show real-time progress (e.g., "Parsing CV content..." → "Analyzing skills..."). Implementing event streaming manually over a chain of functions would require significant boilerplate.

4. **Testability**: The graph structure makes it easy to test individual nodes in isolation or the full pipeline. We can mock any node and verify the state passes correctly.

That said, for this project's linear pipeline, LangGraph is somewhat over-engineered. The real value would show if we add parallel branches (e.g., analyzing both the CV and a cover letter simultaneously) or loops (e.g., re-scraping jobs if the first search returns too few results).

### Q2: "How do you prevent SQL injection?"

We prevent SQL injection in two ways:

1. **Parameterized queries**: All SQL queries use bound parameters (`:param` syntax) instead of string formatting. For example:
   ```python
   query = text("SELECT * FROM jobs_raw ORDER BY published_date DESC LIMIT :limit")
   df = pd.read_sql(query, engine, params={"limit": limit})
   ```
   The database driver handles escaping, so even if `limit` contains malicious SQL, it is treated as a value, not as code.

2. **ORM queries**: The `analysis_history` queries use SQLAlchemy's ORM API:
   ```python
   db.query(AnalysisHistory).filter(AnalysisHistory.user_id == user.id).all()
   ```
   The ORM generates parameterized queries automatically. The `user.id` value is never concatenated into a SQL string.

3. **User input validation**: All API inputs are validated by Pydantic schemas before reaching any database code. Email strings are validated with `EmailStr`, string lengths are bounded by column definitions (e.g., `String(320)` for email), and filenames are validated for allowed extensions.

### Q3: "What happens if the LLM returns bad JSON?"

This is handled at multiple levels:

1. **JSON cleaning**: In both `cv_analyzer` and `job_matcher`, the raw LLM output is cleaned before parsing:
   ```python
   clean = last_message
   if "```json" in clean:
       clean = clean.split("```json")[1].split("```")[0].strip()
   elif "```" in clean:
       clean = clean.split("```")[1].split("```")[0].strip()
   ```
   This handles the common case where the LLM wraps JSON in markdown code blocks.

2. **Try/except with error state**: The JSON parsing is wrapped in a try/except block. If parsing fails, the agent sets `state.error` instead of crashing the pipeline:
   ```python
   except Exception as e:
       state.error = f"Error analyzing CV: {str(e)}"
   ```
   The pipeline's `should_continue` function then detects the error and stops execution, returning the error to the user.

3. **Fallback defaults**: The code uses `.get()` with defaults when extracting fields from the parsed JSON:
   ```python
   strengths=parsed.get("strengths", []),
   ats_score=ats_data.get("ats_score", 0),
   ```
   So even if the JSON structure is wrong, the system degrades gracefully rather than crashing.

4. **Prompt engineering**: The prompts explicitly instruct the LLM to "Return JSON only, no extra text" and provide the exact expected JSON schema. This significantly reduces malformed responses in practice.

### Q4: "How does your rate limiting work?"

We use the `slowapi` library, which implements a sliding window rate limiter:

```python
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

- Each request is tracked by the client's IP address (extracted from `X-Forwarded-For` or the direct remote address).
- A sliding window of 60 seconds is maintained. If a client exceeds 60 requests in that window, the server returns HTTP 429 (Too Many Requests).
- Individual endpoints can override the default limit using decorators:
  ```python
  @app.get("/api/v1/health")
  @limiter.limit("30/minute")
  ```
- The CV analysis endpoints are limited to 5/minute to prevent abuse of the LLM API (which costs money per call).

This protects the server from DoS attacks and prevents a single user from exhausting the LLM API budget.

### Q5: "Why FAISS instead of a normal database search?"

(Full answer in Section 6 above, but here is a concise version for the defense.)

FAISS enables **semantic search** — matching based on meaning, not exact keywords. A SQL query for "Python" will miss a job that says "Django experience required." FAISS will catch it because the embeddings for "Django" and "Python" are close in vector space.

The BGE-small embedding model converts text into 384-dimensional vectors. These vectors capture the *context* and *meaning* of words, not just their literal presence. This is especially important for job matching because:
- Job titles rarely use the same words as skill lists.
- Candidates and employers describe the same skills differently.
- Related skills (e.g., "FastAPI" and "Django") should match even though they are different strings.

We use FAISS specifically (not Pinecone or Weaviate) because:
- The entire index (~10,000 jobs) fits in ~150MB of RAM.
- FAISS runs locally on CPU with sub-10ms query times.
- No external service or API key is needed.
- It is free and open source.

### Q6: "How is the password stored securely?"

We rely on fastapi-users, which internally uses `passlib` with the `bcrypt` hashing algorithm:

1. When a user registers, the plain-text password is immediately hashed using bcrypt with a salt (random data added before hashing).
2. Only the hash is stored in the `hashed_password` column of the `users` table.
3. When a user logs in, the server takes the provided password, hashes it with the same salt, and compares it to the stored hash.
4. Bcrypt is intentionally slow (~100ms per hash) to make brute-force attacks impractical.
5. The plain-text password is never logged, returned in API responses, or stored anywhere.

Additionally, the JWT secret (`AUTH_JWT_SECRET` in `.env`) is a long, random string generated specifically for this application. The JWT itself uses HS256 (HMAC with SHA-256) for signing.

Note: This project does not implement password reset or email verification flows, though fastapi-users supports them. These would require email sending infrastructure.

### Q7: "What is your test coverage?"

The project has three test files:

**`tests/test_api.py`** (106 lines, 14 tests):
- Tests that all endpoints exist and return correct status codes.
- Tests input validation (missing file, wrong extension, file too large).
- Tests that protected endpoints reject unauthenticated requests.
- Tests rate limiting (sends 35 requests to a 30/min endpoint, expects 429).

**`tests/test_agents.py`** (478 lines, 15 tests):
- Tests the core ATS scoring algorithm as a pure function (no LLM needed) — covers perfect CV, poor CV, personal info detection, missing sections, long CV.
- Tests the report builder with mocked LLM — covers successful report, missing analysis, missing jobs, zero scores, no ATS result.
- Tests the job matcher with mocked LLM and retriever — covers successful matching, missing analysis, empty results.
- Tests workflow control flow (should_continue with/without error).
- Tests schema serialization roundtrips.

**`tests/test_file_handler.py`** (22 lines, 1 test):
- Tests PDF file parsing with a minimal valid PDF.

The tests use mocking for LLM calls and FAISS to avoid external dependencies and API costs. The API tests use SQLite in-memory database. Coverage is approximately:
- Agent logic: ~90% (core ATS scoring is well-tested)
- API routes: ~80% (each endpoint has at least one test)
- File handling: ~60% (PDF tested, DOCX not tested)
- Frontend: 0% (no frontend tests exist)

This is a known gap. For a production system, we would add:
- Frontend component tests (Vitest + React Testing Library).
- Integration tests with a test PostgreSQL database.
- End-to-end tests (Playwright or Cypress).

### Q8: "How would this scale to 10,000 users?"

**Current limitations:**
- The PostgreSQL database (Neon free tier) has a 500MB limit and 60 concurrent connections.
- The LLM API (Groq) has rate limits (typically 30 requests per minute on the free tier).
- The FAISS index is loaded in memory on a single server.
- The file system stores uploaded CVs temporarily.

**Scaling strategies:**

1. **Database**: Upgrade to a paid PostgreSQL tier with more connections and storage. Add connection pooling (PgBouncer) to handle thousands of concurrent connections.

2. **LLM API costs**: At 4 LLM calls per analysis and ~10,000 analyses/day, that is 40,000 calls/day. Groq pricing for Llama 3.3-70B is approximately $0.59/1M tokens. If each analysis uses ~4K tokens, total cost would be ~$0.09/day — very affordable.

3. **Horizontal scaling of the API**: Deploy behind a load balancer (e.g., AWS ALB) with multiple FastAPI instances. The JWT-based auth is stateless, so any instance can handle any request. Rate limiting would need to use a shared Redis backend instead of per-instance memory.

4. **FAISS**: Load the FAISS index once at startup (it is currently cached in a global variable). For larger datasets, use a sharded index or switch to a vector database like Pinecone/Qdrant.

5. **File storage**: Move uploaded files to S3 or Cloud Storage instead of the local filesystem.

6. **Caching**: Add Redis caching for frequently accessed data (recent jobs, user profiles) to reduce database load.

7. **Background processing**: Use a task queue (Celery + Redis) for CV analysis so users do not have to wait for the HTTP response. Send results via webhook or polling.

The biggest bottleneck is the LLM API rate limit. At scale, we would either upgrade to a paid Groq tier, cache analysis results for similar CVs, or use a local open-source model (e.g., Llama 3B quantized) for the simpler tasks.

### Q9: "How do you handle concurrent file uploads?"

The `api.py` saves each uploaded file to a unique temporary file using Python's `tempfile.NamedTemporaryFile`:

```python
with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
    tmp.write(contents)
    tmp_path = tmp.name
```

This guarantees unique filenames even under concurrent uploads. The temporary file is deleted in the `finally` block after processing. The analysis pipeline runs synchronously within the request (or within a thread for the streaming endpoint).

The backend runs with `uvicorn` (ASGI server), which handles concurrent requests using async workers. By default, uvicorn uses a single process with async task scheduling. For higher concurrency, we would use `uvicorn --workers 4` to spawn multiple processes.

The SQLAlchemy session is request-scoped — each request creates its own `SessionLocal()` instance and closes it when done. This prevents cross-request data contamination.

### Q10: "What is the purpose of the FAISS integrity check?"

The FAISS index files are serialized Python objects (via pickle). Loading a malicious FAISS file could execute arbitrary code. The `_verify_faiss_integrity()` function computes a SHA-256 hash of all index files and compares it to a stored hash in `.faiss_hash`:

```python
def _verify_faiss_integrity() -> bool:
    # Walk all files in FAISS_DIR, hash them, compare to stored hash
    hasher = hashlib.sha256()
    for root, _dirs, files in os.walk(FAISS_DIR):
        for fname in sorted(files):
            if fname == ".faiss_hash":
                continue
            path = os.path.join(root, fname)
            with open(path, "rb") as f:
                hasher.update(f.read())
    return hasher.hexdigest() == stored.get("sha256")
```

If the hash does not match (meaning the files were modified or replaced), the system refuses to load the index unless `FAISS_ALLOW_DANGEROUS=true` is set in `.env`. This protects against:
- Accidental corruption of the index files.
- Malicious replacement of the index by an attacker with filesystem access.

For development convenience, the `.env` has `FAISS_ALLOW_DANGEROUS=true` so the check is bypassed. In production, admin should disable this and rely on the integrity hash.

### Q11: "How does the streaming endpoint work?"

The streaming endpoint (`/api/v1/analyze-cv/stream`) uses Server-Sent Events (SSE), a standard HTTP mechanism where the server sends multiple events over a single long-lived connection.

The flow is:
1. Frontend sends a POST request with the file.
2. Backend validates the file and saves it temporarily.
3. Backend creates an async generator (`event_generator`) that runs the LangGraph pipeline in a thread pool executor (`loop.run_in_executor`).
4. As each LangGraph node completes, the generator yields an SSE event:
   ```
   data: {"step": "parser", "status": "complete"}

   data: {"step": "analyzer", "status": "complete"}

   data: {"step": "complete", "result": {...}}
   ```
5. The response uses `StreamingResponse` with `media_type="text/event-stream"` and headers to disable buffering.
6. The frontend reads the stream using the Fetch API's `response.body.getReader()` and parses each `data:` line.
7. If the user navigates away, the `AbortController` cancels the request and the temporary file is cleaned up.

SSE was chosen over WebSockets because it is simpler (plain HTTP, no upgrade), works through all proxies, and the communication is unidirectional (server → client), which is all we need.

### Q12: "Why two analyze-cv endpoints (regular and stream)?"

The regular endpoint (`POST /api/v1/analyze-cv`) runs the full pipeline synchronously and returns all results at once. It is simpler for programmatic API clients.

The streaming endpoint (`POST /api/v1/analyze-cv/stream`) sends progress updates as each agent completes. It is designed for the frontend to show real-time progress indicators (spinning icons, step-by-step labels).

Having both gives flexibility: API clients can use the simple one, while the web UI benefits from streaming. The underlying pipeline code (`_run_pipeline`) is shared — the regular endpoint calls `graph.invoke()` (blocks until done), while the streaming endpoint calls `graph.stream()` (yields per-node).

### Q13: "What is the ATS score algorithm? Is it really useful?"

The ATS score is computed by the `ats_checker` tool in `cv_analyzer.py`. It is a **deterministic, rule-based** algorithm — no LLM is involved in the scoring itself.

The score has four equally-weighted components (25% each):

1. **Format (25%)**: Checks for tables (-30), images (-20), and font count (>3 fonts: -20, >2 fonts: -10). These are known ATS pitfalls — most ATS software cannot parse text inside tables or images, and inconsistent fonts confuse parsers.

2. **Structure (25%)**: Checks for required sections (-25 each for missing experience, education, or skills), dates in experience (-15), and summary/objective (-10). ATS systems expect standard section headers to categorize content correctly.

3. **Content (25%)**: Checks for action verbs (<3 verbs: -25, <6 verbs: -10), personal information (-20 for things like date of birth, nationality, marital status, religion, photo — which can cause bias and are often stripped), and quantifiable achievements (-15 if no numbers found).

4. **Length (25%)**: Penalizes CVs shorter than 1 page (-50) or longer than 2 pages (-30). One to two pages is the industry standard.

**Is it really useful?** Yes, but with caveats. The score is a heuristic — it captures known ATS best practices, but different ATS software (Workday, Taleo, Greenhouse) behave differently. The real value is not the number itself, but the **specific issues** list: "Tables detected", "Missing Education section", "Too few action verbs". These give the user concrete, actionable feedback. The score also serves as a benchmark — users can upload an improved CV and see if the number goes up.

The algorithm is deliberately transparent and explainable. Unlike a machine learning model, we can tell the user exactly why their score is low and what to fix.

### Q14: "What security measures are in place beyond authentication?"

1. **Input validation**: All API inputs are validated by Pydantic schemas. File types are restricted to PDF/DOCX. File size is limited to 10MB. The `limit` parameter in queries is bounded by the endpoint logic.

2. **File handling**: Uploaded files are saved to temporary files (not user-writable paths). Filenames are not used for filesystem operations — only the safe `tempfile` path is used. Temporary files are deleted in `finally` blocks to prevent disk space exhaustion.

3. **FAISS deserialization safety**: The FAISS index integrity check (SHA-256 hash) prevents loading tampered pickle files. The `allow_dangerous` flag must be explicitly enabled.

4. **JWT security**: Tokens expire after 1 hour. The signing secret is stored in `.env` (not in code). The algorithm is HS256 (not the weaker HS512 or no-algorithm options).

5. **CORS**: The API allows all origins (`allow_origins=["*"]`). This is acceptable for a public API but would be restricted in production to specific domains.

6. **Rate limiting**: Prevents brute force attacks on login and resource exhaustion on the LLM API.

7. **Error handling**: Production errors return generic "Internal Server Error" messages without exposing stack traces. Sentry can be enabled for server-side error tracking without leaking details to clients.

8. **Secrets management**: All secrets (JWT secret, database URL, API keys) are in `.env`, which is listed in `.gitignore` and never committed.

**What is NOT implemented yet**: HTTPS termination (would use a reverse proxy like nginx), SQL injection prevention at the ORM level is adequate but not audited, no CSRF protection (not needed for token-based auth), no input sanitization for XSS (the frontend reacts to this, not the API).

### Q15: "Why does the frontend use static imports and not code splitting?" (Resolved in v0.3.0)

This was originally a known limitation — the entire frontend was bundled into a single JS file. In v0.3.0, we implemented code splitting using `React.lazy()`:

```tsx
const AnalysisPage = React.lazy(() => import('@/pages/AnalysisPage'))
const DashboardPage = React.lazy(() => import('@/pages/DashboardPage'))
// etc.
```

Each route now loads its page component as a separate chunk via `Suspense` with a fallback spinner. This reduced the initial bundle size from a single large file to smaller, on-demand chunks (LoginPage: 4.5kB, AnalysisPage: 18.8kB, DashboardPage: 178kB). The trade-off is a brief loading indicator when navigating to a new route for the first time.

### Q16: "What new features were added in v0.3.0?"

v0.3.0 focused on three areas: new AI-powered job tools, frontend UX improvements, and bug fixes.

**New Endpoints:**
- **Match Job** (`/api/v1/jobs/match-job` and `/file`): Match an analyzed or fresh CV against the job database or a specific job ID. Uses the existing two-stage retrieval (FAISS + LLM re-scoring).
- **Tailor Resume** (`/api/v1/jobs/tailor-resume`): Given a CV analysis and a job description, rewrite the experience section to emphasize matching keywords and achievements.
- **Stand Out** (`/api/v1/jobs/stand-out`): Generate personalized suggestions for how a candidate can differentiate themselves for a specific role.
- **Cover Letter** (`/api/v1/jobs/cover-letter`): Generate a professionally formatted cover letter based on the CV analysis and target job.
- **Rewrite Suggestions** (`/api/v1/skills/rewrite-suggestions`): Analyze individual CV bullet points and suggest specific rewrites for stronger impact.
- **Market Demand** (`/api/v1/skills/market-demand`): Evaluate which skills are in demand for a given job description versus which the candidate lacks.

**New Frontend Pages:**
- **Job Match Page** (`/job-match`): Select an analysis, pick between "Find Jobs," "Tailor Resume," "Stand Out," or "Cover Letter," and view results in a dedicated results panel.
- **Mobile responsive navbar**: Hamburger menu with drawer for mobile devices.
- **Protected route refactoring**: All protected pages use a reusable `ProtectedRoute` wrapper that checks auth and redirects to /login if unauthenticated.

**Accessibility & Code Quality:**
- Code splitting with `React.lazy()` for all route components.
- `aria-label` attributes on all interactive elements (pagination, toast dismiss, nav, password toggle).
- `role="alert"` on error banners for screen reader announcements.
- Removed `tabIndex={-1}` from password toggle buttons, added `aria-label` to all icon-only buttons.

**Bug Fixes:**
- Fixed: Rate limit testing endpoint had wrong path (`api/v1/analyze-cv` → `api/v1/analyze-cv/stream` for `test_rate_limiting`).
- Fixed: FAISS retriever used incorrect response field (`job_title` vs `title`), fixed to match knowledge graph schema.
- Fixed: Missing `/rewrite-suggestions` route caused 404 in `api.py`.
- Fixed: LangGraph pipeline error handling — streaming pipeline now catches `json.JSONDecodeError` from malformed LLM responses and surfaces a user-friendly error.
- Fixed: Logout button visible on mobile login page (hidden when not authenticated).
- Fixed: Navigation items duplicated in mobile drawer.
- Fixed: History page missing "no analyses" guidance for first-time users.

**API Response Consistency:**
- Normalized all new endpoint response schemas to include `success: bool` and `data: dict` wrapping (matching the existing streaming endpoint pattern).
- All endpoint-level errors return `{"detail": "..."}` strings (matching FastAPI convention).

---

# 10. Known Limitations (Future Work)

## Authentication & User Management
- **No email verification**: Users can register with any email, even non-existent ones. Adding email verification (fastapi-users supports it) would improve security.
- **No password reset**: If a user forgets their password, there is no way to reset it. Would require an email sending service (SendGrid, AWS SES).
- **No admin dashboard**: There is no interface for managing users, viewing analytics, or monitoring system health. The `is_superuser` flag exists in the schema but has no admin UI.
- **No OAuth/social login**: Users can only register with email/password. Adding Google or LinkedIn login would improve user adoption.

## Testing
- **No frontend tests**: The frontend has zero tests. Unit tests for components (Vitest + React Testing Library) and end-to-end tests (Playwright) should be added.
- **Limited API integration tests**: API tests use SQLite in-memory database, not the production PostgreSQL. True integration tests with a test database would catch more issues.
- **No load testing**: The system has not been tested under concurrent load from multiple users.

## AI & LLM
- **No fallback if Groq is down**: The system depends entirely on Groq's API. If Groq is unavailable, analysis fails. A fallback to another provider (e.g., OpenAI, or a local model) would improve reliability.
- **No caching of analysis results**: If two users upload similar CVs, the system re-analyzes both from scratch. Caching results (keyed by a hash of the CV text) would save costs and improve response times.
- ~~**No streaming in LangGraph error handling**~~ ✅ **Resolved in v0.3.0**: Streaming pipeline now catches `json.JSONDecodeError` from malformed LLM responses and surfaces a user-friendly error instead of crashing the connection.
- **No prompt versioning**: The LLM prompts are hardcoded in the agent files. A prompt management system would allow A/B testing and rollback of prompts.

## Job Matching & Data
- **Static FAISS index**: The job index is built from a static CSV file. To add new jobs, someone must re-run `ingest.py` manually. A scheduled refresh pipeline would keep the index current.
- **No real-time LinkedIn scraping**: The `scrapers` directory contains a LinkedIn scraper, but it has not been integrated into the analysis pipeline. LinkedIn's Terms of Service also prohibit automated scraping. Future versions would use official APIs (LinkedIn Jobs API, Indeed API) instead.
- **FAISS hash bypass for development**: The `.env` has `FAISS_ALLOW_DANGEROUS=true`, which disables the integrity check. In production, this should be set to `false`.

## Performance & Scaling
- **Single server**: The entire API runs as a single uvicorn process. For high availability, it should be deployed behind a load balancer with multiple instances.
- **No Redis caching**: Frequently accessed data (recent jobs, user stats) could be cached in Redis to reduce database load.
- **No background task queue**: CV analysis runs synchronously in the HTTP request. For high traffic, it should be offloaded to a background worker (Celery) and the frontend should poll for results.
- **10MB file limit**: Hardcoded maximum. Some CVs with embedded images or portfolios exceed this. A configurable limit or cloud storage integration would be better.

## Frontend (Addressed in v0.3.0)
- ~~**No code splitting**~~ ✅ **Resolved**: Routes now use `React.lazy()` for dynamic imports (LoginPage: 4.5kB, AnalysisPage: 18.8kB, DashboardPage: 178kB separate chunks).
- ~~**No mobile hamburger menu**~~ ✅ **Resolved**: Navbar now has a responsive mobile drawer with hamburger toggle, auth buttons included.
- ~~**No accessibility support**~~ ✅ **Resolved**: All error banners have `role="alert"`, password toggles have `aria-label` and removed `tabIndex={-1}`, toast dismiss and pagination buttons have `aria-label`, nav has `aria-label`/`aria-current`.
- **No offline support**: The app requires a continuous internet connection. A service worker could cache static assets and enable offline access.
- **No i18n**: The UI is English-only. Internationalization (react-i18next) would make it accessible to Arabic-speaking users (relevant for this market).
- **No PWA support**: The app cannot be installed on a mobile device as a native-like app. Adding a manifest.json and service worker would make it a Progressive Web App.

## Monitoring & Operations
- **Sentry is optional**: Error tracking requires `SENTRY_DSN` to be set, which is blank by default. No formal SLI/SLO monitoring exists.
- **No structured logging**: The `logging.basicConfig` setup is minimal. Structured logging (JSON format with request IDs) would make debugging in production easier.
- **No CI/CD pipeline**: The `.github` directory exists but does not contain a deployment workflow. The project should have automated tests and deployment (GitHub Actions).

---

*This document was generated based on the actual source code of CVision v0.3.0. All explanations refer to real code paths, data models, and configurations in the repository.*
