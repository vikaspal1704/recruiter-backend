# MIGRATION_NOTES — existing codebase → polished recruiter API

Ground truth from clone of `vikaspal1704/recruiter-backend` (docs authored 2026-09-21 IST).

---

## 1. What exists today

### Entry & cross-cutting

| Path | Notes |
|---|---|
| `app.py` | FastAPI title **"Lovable AI MVP Backend"**; CORS `*`; includes **only** `resume` + `search`; defines unused `get_current_user`; `GET /healthcheck` |
| `dependencies.py` | Bearer→Supabase `get_current_user` (canonical candidate) |
| `supabase_client.py` | Service-role client; **prints URL + key prefix** — remove |
| `requirements.txt` | FastAPI, Supabase, Pinecone, OpenAI, SendGrid, PyPDF2, pytest, uvicorn, … |
| `.gitignore` | Only `.env` and `venv` — incomplete |
| No README, LICENSE, Docker, CI, tests, `.env.example` | Add in Phase 1 |

### Routes

| Path | Wired? | Code quality |
|---|---|---|
| `routes/resume.py` | **Yes** | Working MVP; `DUMMY_USER_ID`; inline Pydantic model |
| `routes/search.py` | **Yes** | Working MVP; uses `.error` on execute result — verify against supabase-py version |
| `routes/outreach.py` | No | Logic present; **missing `get_current_user` import** |
| `routes/profile.py` | No | Logic present; missing import; **triplicate** `from supabase_client import supabase` |
| `routes/background.py` | No | Stub flow; missing import |
| `routes/auth.py` | No | **Empty file (0 bytes)** |
| `routes/analytics.py` | No | **Empty file (0 bytes)** |

### Schemas

All of `schemas/resume.py`, `search.py`, `outreach.py`, `profile.py`, `background.py` are **empty (0 bytes)**. Models currently live inside route modules.

### Services — KEEP

| Path | Role |
|---|---|
| `services/resume_parser.py` | PDF download + PyPDF2 + OpenAI JSON parse |
| `services/embedding_service.py` | OpenAI embeddings + Pinecone `candidates-mvp` |
| `services/email_service.py` | SendGrid send |
| `services/background_check_service.py` | Stub “passed” report |
| `services/analytics_service.py` | PostHog capture (optional) |
| `services/qa_generator.py` | GPT pre-screen questions (unused by routes) |

### Junk — DELETE

| Path | Action |
|---|---|
| `__pycache__/` (root, `routes/`, `services/`) | Delete; gitignore |
| `Java.pdf` (~187KB) | Delete — unrelated sample |
| `React.pdf` (~182KB) | Delete — unrelated sample |

If a PDF fixture is needed later, add a **tiny** `tests/fixtures/sample_resume.pdf` deliberately.

---

## 2. What to keep (do not casually rewrite)

- Resume upload → Storage → `resumes` insert flow
- Parse → `candidate_profiles` → Pinecone upsert flow
- Search → embed query → Pinecone → hydrate profiles
- Integration choices: Supabase + Pinecone + OpenAI (+ SendGrid)
- Health path name `/healthcheck` (already used)
- Router prefixes `/resume`, `/search`, `/outreach`, `/profile`, `/background`

---

## 3. What to change

| Change | Why |
|---|---|
| Rename app title | Portfolio branding; drop “Lovable AI MVP” |
| Enforce auth | Portfolio quality MUST |
| Wire outreach/profile | Features already written |
| Fix missing imports | Routers crash if included as-is |
| Env-based CORS | `*` is demo-hostile for “prod profile” |
| Lazy/test-safe clients | pytest cannot hit real Pinecone on import |
| Fill or remove empty schemas/auth/analytics | Ambiguity wastes agent time |
| Expand gitignore + purge bytecode/PDFs | Hygiene |
| Add docs/Docker/CI/tests/demo | Recruiter-ready |

---

## 4. What to delete

| Item | Justification |
|---|---|
| `__pycache__/**` | Never commit bytecode |
| `Java.pdf`, `React.pdf` | Not required for API; bloat |
| Duplicate `get_current_user` in `app.py` | Single source in `dependencies.py` |
| Empty `routes/auth.py` / `analytics.py` | Only if not implementing in Phase 2 — **or** implement; do not leave forever-empty |
| Empty `schemas/*` | Only if deciding to keep models inline permanently |

**Do not delete** working `resume.py` / `search.py` / core services without Phase justification.

---

## 5. Rename checklist

| From | To |
|---|---|
| FastAPI `title="Lovable AI MVP Backend"` | `title="Recruiter Talent Search API"` (or `Recruiter Backend`) |
| README product framing | Recruiter / talent-search API |
| Optional: Docker image name | `recruiter-backend` |

GitHub repo name `recruiter-backend` can stay.

---

## 6. Data / env migration notes for operators

1. Create `.env` from `.env.example` (never commit).  
2. Ensure Supabase tables/bucket exist as used by current code (`resumes`, `candidate_profiles`, `profiles`, `outreach_logs`, `background_checks`, bucket `resumes`).  
3. Pinecone index `candidates-mvp` dim 1536 cosine — code auto-creates if missing (side effect; consider gating).  
4. Rotate any keys that may have been logged or committed historically.  
5. After enabling auth, old unauthenticated clients will receive `401` — expected.

---

## 7. Known defects to fix while migrating

1. `outreach` / `profile` / `background`: undefined `get_current_user`.  
2. `profile.py`: duplicate imports.  
3. `supabase_client.py`: secret prefix stdout.  
4. `embedding_service.py`: network side effect at import.  
5. `email_service.py`: hardcoded `from_email="noreply@yourdomain.com"` — move to env.  
6. Resume auth bypass + dummy user id.  
7. Search may assume `.error` attribute depending on supabase-py API — validate in tests.

---

## 8. Mapping phases → file touch list

| Phase | Likely files |
|---|---|
| 1 | `.gitignore`, `app.py` (title only), `supabase_client.py`, `.env.example`, `Dockerfile`, `docker-compose.yml`, `.github/workflows/ci.yml`, `README.md`, `LICENSE`, delete PDFs/pycache |
| 2 | `dependencies.py`, `app.py`, `routes/*.py`, `schemas/*.py`, CORS/auth config |
| 3 | `tests/**`, possibly lazy-init in services |
| 4 | `scripts/demo.sh`, README demo section |

---

## 9. Success snapshot

After migration, a recruiter should see:

- Clear README + MIT license  
- No junk binaries/bytecode  
- Auth-protected talent API  
- Docker + CI  
- Documented upload → parse → search (+ optional outreach)  

…while recognizing it remains an **MVP portfolio backend**, not a full ATS.
