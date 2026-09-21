# PRD — Recruiter / talent-search API

**Product:** Hire-ready portfolio backend for talent search  
**Owner:** Vikas Pal  
**Audience:** Recruiting engineers evaluating SWE craft; coding agents polishing the repo  
**Status:** MVP → polished portfolio demo

---

## 1. Problem

Recruiters and hiring managers need a thin API that can:

1. Ingest a candidate resume (PDF)
2. Extract structured profile fields
3. Search candidates by natural-language query (semantic)
4. Optionally email a candidate

The existing codebase already prototypes this, but is framed as “Lovable AI MVP”, lacks README/Docker/CI/tests, bypasses auth, and leaves several routers unwired or empty. That undermines portfolio signal.

## 2. Goals

### 2.1 Primary goal

Ship a **clear, documented, runnable** FastAPI service that demonstrates production-minded backend craft on top of real integrations (Supabase, Pinecone, OpenAI, SendGrid).

### 2.2 Success metrics (portfolio)

- Recruiter can clone, configure `.env` from `.env.example`, run via Docker or uvicorn, hit `/docs`, and complete upload → parse → search in &lt; 15 minutes.
- Auth required on non-health endpoints (or clearly gated behind a documented demo mode flag that defaults **off** in production config).
- CI green on PR (lint optional; tests + Docker build required).
- No secrets, bytecode, or junk PDFs in the default branch.

---

## 3. Requirements

### MUST

| ID | Requirement |
|---|---|
| M1 | Rename app title away from “Lovable AI MVP Backend” to recruiter/talent-search branding |
| M2 | Document and keep: `POST /resume/upload`, `POST /resume/parse/{resume_id}`, `GET /search/`, `GET /healthcheck` |
| M3 | Auth on mutating and PII routes: API key **or** Bearer JWT (Supabase); health may remain public |
| M4 | `.env.example` with all required vars, **no secret values** |
| M5 | Harden `.gitignore`; remove committed `__pycache__/` and junk `Java.pdf` / `React.pdf` |
| M6 | README that is honest about MVP status and links to `/docs/*` |
| M7 | Dockerfile + compose (or documented single-container run) |
| M8 | GitHub Actions CI: install, pytest, optional Docker build |
| M9 | Pytest suite for health, auth rejection, and core resume/search with mocks |
| M10 | Stop printing secrets / key prefixes at import time |
| M11 | CORS not `*` for documented “production” profile (dev may allow localhost) |

### SHOULD

| ID | Requirement |
|---|---|
| S1 | Wire `outreach` router (SendGrid) behind auth |
| S2 | Wire `profile` router behind auth; fix missing `get_current_user` import |
| S3 | Populate `schemas/` with shared Pydantic models (files are empty today) |
| S4 | Replace `DUMMY_USER_ID` with authenticated user id when auth is on |
| S5 | Structured error responses + consistent status codes |
| S6 | Demo script (`scripts/demo.sh` or `make demo`) exercising happy path |
| S7 | Rate-limit or size-limit PDF uploads (e.g. max 5–10 MB) |
| S8 | Healthcheck optionally reports dependency readiness (Supabase/Pinecone) without leaking secrets |

### COULD

| ID | Requirement |
|---|---|
| C1 | Wire background-check stub route (keep stub; label as demo) |
| C2 | Analytics via PostHog (`analytics_service` exists) behind a feature flag |
| C3 | Pre-screen Q&A endpoint using `qa_generator` |
| C4 | Soft-delete / candidate list pagination |
| C5 | OpenAPI examples and tagged “Recruiter Demo” collection |
| C6 | Implement non-empty `routes/auth.py` (signup/login helpers) if Supabase Auth UX is desired |

---

## 4. Non-goals

- Building a full ATS or LinkedIn competitor
- Guaranteeing production SLAs, multi-region HA, or SOC2
- Real third-party background checks (Checkr etc.) in v1
- A React/Next frontend in this repository
- Changing cloud vendors for the sake of novelty
- Committing real candidate PII or production credentials

---

## 5. Personas

1. **Recruiter reviewer** — clones repo, reads README, tries `/docs`, judges clarity and security hygiene.
2. **Coding agent** — executes AGENT_BRIEF phases; needs unambiguous contracts.
3. **Author (Vikas)** — demo in interviews; needs one-command run + scripted happy path.

---

## 6. User journeys

### Journey A — Ingest & search

1. Authenticate (API key / Bearer).
2. Upload PDF → `resume_id`.
3. Parse → candidate profile + vector upsert.
4. Search with job-like query → ranked list with scores.

### Journey B — Outreach (SHOULD)

1. Search finds candidate.
2. `POST /outreach/` with subject/body → email sent + logged.

---

## 7. Risks & mitigations

| Risk | Mitigation |
|---|---|
| OpenAI/Pinecone cost during demos | Mock in unit tests; sandbox keys; small top_k |
| Service-role key misuse | Never expose to client; auth on API; no key logging |
| Empty schemas / broken unwired routes | Wire carefully; fix imports; tests before enable |
| Accidental secret commit | `.gitignore`, CI secret scan optional, strip DEBUG prints |

---

## 8. Timeline (agent phases)

See [AGENT_BRIEF.md](AGENT_BRIEF.md):

1. Hygiene + README/Docker/CI  
2. Wire routers + auth  
3. Tests  
4. Demo script

---

## 9. Open questions (resolve during Phase 2)

- Prefer **static API key** (simpler portfolio) vs **Supabase Bearer only** vs both?
  - **Recommendation:** both — `X-API-Key` for demos + Bearer for Supabase-aligned path; document clearly.
- Keep Pinecone index name `candidates-mvp` or rename to `candidates`?
  - **Recommendation:** keep `candidates-mvp` for continuity; document in `.env.example` as overrideable `PINECONE_INDEX_NAME`.
