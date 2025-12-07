# Job Market Agent — Architecture Overview

- Purpose: AI-powered pipeline that analyzes a CV, finds matching jobs, generates tailored CVs and cover letters, prepares interview materials, and tracks applications.
- Core parts: `frontend` (React + Appwrite Auth), `api_server.py` (Flask API), `agents` (Gemini-based AI agents), `utils` (scraping, CV tailoring, storage), `data` (SQLite + Appwrite).

## System Diagram

```mermaid
graph TD
  A[User Browser] --> B[React Frontend (Vite)]
  B -->|JWT via Appwrite| C[Flask API /api/*]
  C --> D[Agents (Gemini via agno)]
  C --> E[Utilities: Scraper, CV Engine, Tracker]
  C --> F[Appwrite (Auth, DB, Storage)]
  E --> G[SQLite (local tracking)]
  D --> H[Google Gemini]
  E --> I[External Job Boards]
```

## Directory Layout

- `frontend/` — React app (Vite + Tailwind + shadcn/ui)
- `api_server.py` — Flask API with Appwrite integration and protected routes
- `agents/` — Specialized AI agents and an orchestrator
- `utils/` — Job scraping, CV tailoring, PDF generation, Appwrite client, tracking
- `applications/` — Generated artifacts (CVs, cover letters, interview prep)
- `cvs/` — User CV source files
- `tests/` — Test harness and docs
- `.trae/documents/` — prior technical docs (note: backend is Flask here)

## Frontend

- Auth: Appwrite JWT; requests include `Authorization: Bearer <jwt>` built in `frontend/src/utils/api.ts:12`.
- Appwrite client: `frontend/src/utils/appwrite.ts:1` configures `Account`, `Databases`, `Storage` using `VITE_*` env.
- Auth context: `frontend/src/context/AuthContext.tsx:16` provides `login`, `register`, `logout` and user state.

## Backend API (Flask)

- Server: `api_server.py` runs Flask on `http://localhost:8000` with CORS for `http://localhost:5173`.
- Auth middleware: `login_required` verifies Appwrite JWT per request in `api_server.py:73`.
- Key routes:
  - `POST /api/search-jobs` searches and formats jobs using the pipeline (`api_server.py:105`).
  - `POST /api/apply-job` generates CV + cover letter, saves records, returns download paths (`api_server.py:138`).
  - `GET /api/download` streams generated files (`api_server.py:210`).
  - `POST /api/analyze-cv` builds a profile from an uploaded CV, persists to Appwrite (`api_server.py:255`).
  - `POST /api/match-jobs` ranks jobs against the profile and optionally emails matches (`api_server.py:378`).
  - `GET/PUT /api/profile` retrieves or updates structured profile data (`api_server.py:520`, `api_server.py:544`).
  - `GET /health` liveness check (`api_server.py:894`).
- Appwrite collections and buckets: `DATABASE_ID='job-market-db'`, `applications`, `profiles`, `jobs`, bucket `cv-bucket` (`api_server.py:60`).

## Pipeline Workflow

- Entry point class: `JobApplicationPipeline` — `main.py:53`.
- Steps:
  - Load CV: extracts text from PDF or reads text (`main.py:68`).
  - Build profile: delegates to `profile_builder` agent and initializes CV engine (`main.py:99`, `main.py:124`).
  - Search jobs: `AdvancedJobScraper.scrape_jobs` with enrichment and caching (`main.py:135`; utils below).
  - Generate application: tailor CV, export PDF, write cover letter, track application (`main.py:166`).
  - Prepare interview: save interview prep materials (`main.py:255`).
- Returns file paths and stores app metadata via tracker.

## Agents

- Consolidated exports: `agents/__init__.py:6` exposes `profile_builder`, `job_intelligence`, `application_writer`, `interview_prep_agent`, and `orchestrator_agent`.
- Orchestrator: high-level coordinator with tools for finding jobs, optimizing CV, writing letters, preparing interviews (`agents/orchestrator_agent.py:97`).
- Backed by `agno` and Gemini (`agents/orchestrator_agent.py:9`, `agents/orchestrator_agent.py:100`).

## Utilities

- Facade exports: `utils/__init__.py:6` exposes `memory`, `AdvancedJobScraper`, `CVTailoringEngine`, `ApplicationTracker`.
- Job scraping: `utils/scraping.py` — jobspy-based scrape, dedup, clean, enrich, cache, and AI description fallback.
  - Configuration and metrics (`utils/scraping.py:51`, `utils/scraping.py:97`).
  - Advanced pipeline and cache (`utils/scraping.py:842`, `utils/scraping.py:793`).
- CV tailoring: `utils/cv_tailoring.py` — selects template, uses `application_writer` agent, exports via `PDFGenerator`.
  - Tailor CV (`utils/cv_tailoring.py:29`), export PDF (`utils/cv_tailoring.py:198`), cover letter generation (`utils/cv_tailoring.py:299`).
- Tracking: local SQLite tracker for offline and sync to Appwrite when enabled (`utils/tracker.py:6`).
  - Schema setup (`utils/tracker.py:22`), insert and sync (`utils/tracker.py:88`).
- Appwrite client: thin wrapper for Storage and Databases (`utils/appwrite_client.py:8`).

## Data Storage

- Local tracking: SQLite database `applications.db` created on demand (`utils/tracker.py:11`).
- Appwrite:
  - Auth: JWT for per-request identity, set on a fresh client in `login_required` (`api_server.py:85`).
  - Databases: `job-market-db` with `applications`, `profiles`, `jobs` (`api_server.py:60`).
  - Storage: CV and cover letter uploads via `appwrite.input_file` in CV analyze flow (`api_server.py:298`).

## Request Flow

- Login/register in frontend → JWT retrieved (`frontend/src/context/AuthContext.tsx:35`) → requests include `Authorization` (`frontend/src/utils/api.ts:16`).
- Flask verifies JWT and associates `g.user` + `g.client` (`api_server.py:90`).
- Pipeline invoked per action:
  - Search jobs → scraper → formatted response (`api_server.py:115`).
  - Apply job → tailor CV + cover letter → track locally and save to Appwrite (best-effort) (`api_server.py:166`).
  - Analyze CV → build profile → persist profile (`api_server.py:271`).
  - Match jobs → score and email high matches (`api_server.py:461`, `api_server.py:610`).

## Deployment & Runtime

- Backend dev: `python api_server.py` serves at `:8000`.
- Frontend dev: Vite at `:5173`; CORS configured via `CORS_ORIGINS` env.
- Cloud configs: `vercel.json`, `railway.json`, `render.yaml`, `Dockerfile` available for deployment targets.

## Testing

- Test harness and instructions: `tests/README.md:21` and `run_tests.py`.
- Pytest supported; coverage for agents and workflows.

## Notes

- Gemini key polyfill: `GEMINI_API_KEY` and `GOOGLE_API_KEY` are synchronized where needed (`api_server.py:7`, `main.py:20`).
- Files are saved to `applications/` and downloadable via `/api/download` with a `path` query (`api_server.py:210`).
