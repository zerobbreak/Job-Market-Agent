## Objectives
- Deliver a reliable, fast preview of tailored CV + cover letter for any job
- Provide Assisted Apply actions (open job page, copy auto‑fill, email apply) with tracked status
- Lay the foundation for true auto‑apply (browser extension + Playwright automation) without breaking compliance

## Backend Architecture
- Job Queue & Concurrency
  - Introduce a queue (Celery/RQ) for preview/apply jobs; use in‑process threads only as a local fallback
  - Standard job states: queued → running → done | error | cancelled; progress 0–100
- Consistent Response Shapes
  - Preview endpoints always return `{cv_html, cover_letter_html, ats: {score, analysis}}` when `status=done`
  - Apply endpoints return `{files: {cv, cover_letter, interview_prep, form_data}, ats}` and a database record id
- Storage & Downloads
  - Persist artifacts in storage; return signed URLs or cookie‑based `storage/download` with auth
  - Normalize `getDownloadUrl` to support prod base URL and signed links
- Auth & Rate Limits
  - JWT required in prod; dev bypass only when `ALLOW_DEV_NO_AUTH=true` and Appwrite unset
  - Endpoint limits: preview/apply/email per minute; exponential backoff in pollers

## Preview Generation Pipeline
- Profile hydration: cache parsed profile per user; reuse across runs
- CV tailoring: robust JSON extraction with multi‑key fallbacks; sanitize markdown, ensure length > 200 chars
- HTML generation: use `PDFGenerator.generate_html` with templates; include sections (summary/experience/projects/education)
- Fallbacks: if AI disabled or parse fails, generate structured CV from profile + job keywords; always non‑empty
- Progress reporting: 5/25/50/70/95/100 with meaningful phase names
- Streaming option (Phase 2): add SSE endpoint to push progress + partial HTML for faster first paint

## Frontend UX
- Template selection → start preview job; show live percentage and phase name
- Preview rendering in iframe (`srcDoc`) to isolate CSS; tabs for CV and Cover Letter
- Clear errors: timeouts, missing profile/CV, rate‑limit, network; offer retry and return to edit
- Assisted actions visible in header:
  - Open Job Page (tracks `application_started`)
  - Copy Auto‑Fill Data (from `form_data.json` or composed string; tracks `application_autofill_copied`)
  - Confirm & Apply (tracks `application_submitted`)
- Applications page: list artifacts, statuses (pending/applied/interview/rejected), and links

## Assisted Apply Features
- Email Apply endpoint
  - Compose email with tailored CV/CL (HTML attachments or PDFs if toolchain available)
  - Extract recipient email from job or description; log status to Applications
- Auto‑Fill Data
  - Generate structured `form_data.json` and expose Copy action; add per‑ATS field maps over time

## Auto‑Apply Roadmap (Real‑World)
- Browser Extension (Phase 1)
  - Content scripts for Lever, Greenhouse, Workable; fill fields, upload files, submit; user session handles MFA
  - Selector mapping repo; versioned adapters; per‑site QA
- Playwright Automation Service (Phase 2)
  - Headless Chromium; site adapters; login vault; retries; screenshot logs
  - Human‑in‑loop for MFA/captcha; service endpoints: start/status/cancel

## Security & Compliance
- Secrets in vault; never log JWTs/SMTP credentials; PII redaction in logs
- Respect site terms; prefer Assisted Apply unless explicit consent
- Signed URLs for downloads; access scoped per user

## Observability
- Metrics: job durations, success rate, error taxonomy, rate‑limit hits
- Structured logs with job_id; attach progress phase; screenshots for automation service
- Analytics events: `application_started`, `application_submitted`, `application_autofill_copied`, `apply_email_sent`

## Acceptance Criteria
- Preview: always renders non‑empty CV and CL or shows actionable error within < 3 minutes; progress updates visible
- Assisted Apply: Open Job + Copy Auto‑Fill work; Email Apply succeeds when SMTP configured and logs to Applications
- Downloads: CV and CL download from Applications page with secure URLs in prod

## Rollout Plan
- Phase 0: Stabilize preview/apply response shape, progress updates, iframe rendering, dev auth guard
- Phase 1: Assisted Apply UI and email route (already integrated), analytics wiring, signed download URLs
- Phase 2: Browser extension MVP for Lever/Greenhouse; adapter repo and QA harness
- Phase 3: Playwright service with site adapters, audit logs, consent and compliance gates

## Implementation Outline in This Repo
- Backend
  - Introduce queue abstraction; wrap preview/apply jobs; unify response schemas
  - Signed URL generation for `storage/download`
  - Email Apply route with SMTP config and Applications logging
- Frontend
  - Iframe preview tabs; progress bar + phase text
  - Assisted Apply buttons; analytics events; resilient poller (timeout/backoff)
  - Applications page shows statuses and artifact links

Please confirm to proceed with the Phase 0–1 changes now and queue the extension/automation roadmap for Phase 2–3.