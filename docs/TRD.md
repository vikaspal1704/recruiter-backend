# TRD — Technical Requirements Document

**Target:** Polished Recruiter / talent-search API on the **existing** codebase  
**Stack (preserve):** FastAPI, Supabase, Pinecone, OpenAI, SendGrid, PyPDF2, pytest, uvicorn, python-dotenv

---

## 1. Target repository layout

Agents should converge toward this (additive; do not mass-delete working modules):

```text
recruiter-backend/
├── README.md                 # recruiter-facing (from docs pack)
├── AGENTS.md
├── LICENSE                   # MIT © 2026 Vikas Pal
├── .env.example              # no secrets
├── .gitignore                # expanded
├── Dockerfile
├── docker-compose.yml        # optional but SHOULD
├── requirements.txt          # keep; pin or comment strategy
├── pyproject.toml / setup.cfg  # optional
├── app.py                    # FastAPI entry; rename title; include routers
├── dependencies.py           # single auth dependency source of truth
├── supabase_client.py        # no secret logging; lazy or guarded init for tests
├── routes/
│   ├── resume.py             # KEEP (wired)
│   ├── search.py             # KEEP (wired)
│   ├── outreach.py           # wire in Phase 2
│   ├── profile.py            # wire in Phase 2
│   ├── background.py         # COULD wire (stub)
│   ├── auth.py               # implement or delete empty stub intentionally
│   └── analytics.py          # implement or delete empty stub intentionally
├── schemas/                  # fill empty files OR remove and keep models in routes
│   ├── resume.py
│   ├── search.py
│   ├── outreach.py
│   ├── profile.py
│   └── background.py
├── services/
│   ├── resume_parser.py      # KEEP
│   ├── embedding_service.py  # KEEP
│   ├── email_service.py      # KEEP
│   ├── background_check_service.py  # stub OK
│   ├── analytics_service.py  # optional
│   └── qa_generator.py       # COULD expose later
├── tests/
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_auth.py
│   ├── test_resume.py
│   └── test_search.py
├── scripts/
│   └── demo.sh               # Phase 4
├── .github/workflows/ci.yml
└── docs/                     # this documentation pack (copy or submodule link)
```

**Do not** leave `Java.pdf` / `React.pdf` at repo root. **Do not** commit `__pycache__/`.

---

## 2. Environment variables contract

Create **`.env.example`** in the app repo with placeholders only:

```bash
# App
APP_TITLE=Recruiter Talent Search API
APP_ENV=development
API_KEY=change-me-demo-key
# CORS: comma-separated origins; use * only for local throwaway
CORS_ALLOW_ORIGINS=http://localhost:3000,http://localhost:8000
AUTH_MODE=api_key_or_bearer
# AUTH_MODE values: api_key | bearer | api_key_or_bearer | off
# AUTH_MODE=off is for local emergency only; CI and Docker prod profile must not use off

# Supabase
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
# Optional anon key if client-side auth demos are added later
# SUPABASE_ANON_KEY=

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
OPENAI_CHAT_MODEL=gpt-4

# Pinecone
PINECONE_API_KEY=
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=candidates-mvp

# SendGrid (outreach)
SENDGRID_API_KEY=
SENDGRID_FROM_EMAIL=noreply@yourdomain.com

# Optional analytics
# POSTHOG_API_KEY=
# POSTHOG_HOST=https://app.posthog.com
```

### Rules

| Rule | Detail |
|---|---|
| Never commit `.env` | Already partially ignored; keep |
| No real keys in examples | Placeholders only |
| Fail fast on missing required vars | Prefer clear `RuntimeError` **without** printing partial secrets |
| Test mode | Allow mocked clients when `APP_ENV=test` so imports do not require live Pinecone/Supabase |

### Required vs optional at runtime

| Variable | Required for core path | Required for outreach |
|---|---|---|
| `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` | Yes | Yes |
| `OPENAI_API_KEY` | Yes (parse + search) | No |
| `PINECONE_API_KEY`, `PINECONE_ENVIRONMENT` | Yes (parse upsert + search) | No |
| `API_KEY` or valid Bearer | Yes when auth on | Yes |
| `SENDGRID_API_KEY`, `SENDGRID_FROM_EMAIL` | No | Yes |
| PostHog | No | No |

---

## 3. Auth design (MUST)

**Single source of truth:** `dependencies.py` (`get_current_user` / `require_auth`).

Remove duplicate auth function from `app.py` or re-export from `dependencies`.

### Recommended behavior

1. **`AUTH_MODE=api_key_or_bearer` (default for portfolio):**
   - Accept `X-API-Key: <API_KEY>` **or** `Authorization: Bearer <supabase_jwt>`
   - Reject with `401` if neither valid
2. Public: `GET /healthcheck` only (and OpenAPI `/docs` in development)
3. Protect: `/resume/*`, `/search/*`, `/outreach/*`, `/profile/*`, `/background/*`

### Known bugs to fix when wiring

- `routes/outreach.py`, `routes/profile.py`, `routes/background.py` use `Depends(get_current_user)` but **do not import** it → will crash on include.
- Resume uses `DUMMY_USER_ID`; after auth, set `user_id` from authenticated principal (API key principal may be a fixed system UUID documented in `.env.example`).

---

## 4. How to treat existing modules

| Module | Treatment |
|---|---|
| `routes/resume.py` | Keep; add auth Depends; replace dummy user when possible |
| `routes/search.py` | Keep; add auth; fix `cp.error` handling if Supabase client API differs |
| `routes/outreach.py` | Fix import; wire into `app.py`; auth already intended |
| `routes/profile.py` | Fix import + duplicate imports; wire |
| `routes/background.py` | Fix import; optional wire; keep stub service |
| `routes/auth.py` | Empty — implement minimal helpers **or** delete and document “auth via dependency only” |
| `routes/analytics.py` | Empty — wire PostHog events later **or** delete stub |
| `schemas/*` | Empty — populate from inline models in routes |
| `services/embedding_service.py` | Keep; make index name configurable; avoid create-index side effect on import in tests |
| `services/resume_parser.py` | Keep |
| `services/email_service.py` | Keep; read `SENDGRID_FROM_EMAIL` from env |
| `services/qa_generator.py` | Keep unused until COULD endpoint |
| `services/analytics_service.py` | Guard if keys missing |
| `supabase_client.py` | Remove DEBUG prints; consider lazy init |

---

## 5. Docker

### Dockerfile (target)

- Base: `python:3.12-slim`
- `WORKDIR /app`
- Copy `requirements.txt` → `pip install --no-cache-dir`
- Copy application code (not `.env`, not PDFs junk)
- `EXPOSE 8000`
- `CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]`

### docker-compose.yml (SHOULD)

- Service `api` with `env_file: .env`
- Port `8000:8000`
- No need to containerize Supabase/Pinecone (cloud SaaS)

### Health

Compose/K8s can probe `GET /healthcheck`.

---

## 6. CI (GitHub Actions)

Suggested `.github/workflows/ci.yml`:

1. Checkout  
2. Setup Python 3.12  
3. `pip install -r requirements.txt`  
4. `pytest` with `APP_ENV=test` and dummy env vars  
5. `docker build -t recruiter-backend:ci .`

Do **not** inject real production secrets into CI. Mock external calls.

---

## 7. Data stores (existing assumptions)

### Supabase tables (inferred from code)

| Table | Usage |
|---|---|
| `resumes` | `user_id`, `file_url`, `parsed`, `id` |
| `candidate_profiles` | `resume_id`, `name`, `email`, `skills`, `years_experience`, `education`, `raw_text` |
| `profiles` | user profile (`id`, `email`, `full_name`, …) |
| `outreach_logs` | `candidate_id`, `sent_by`, `channel`, `content` |
| `background_checks` | `candidate_id`, `status`, `report_url` |

### Storage

- Bucket: `resumes`

### Pinecone

- Index: `candidates-mvp` (dim 1536, cosine)
- Vector id: candidate profile id
- Metadata: `candidate_profile_id`

Document SQL migrations only if agents add schema changes; do not invent greenfield schema that breaks existing inserts.

---

## 8. Observability

- Replace print-debug with optional `logging` module
- SHOULD: request id middleware (optional)
- COULD: PostHog `track_event` on upload/parse/search

---

## 9. Compatibility constraints

- Prefer FastAPI patterns already used (`APIRouter`, Pydantic models, `UploadFile`)
- Keep `python-multipart` for uploads
- Pytest already in `requirements.txt` — use it
- Do not upgrade major deps casually in polish PRs unless required for security

---

## 10. Deliverables checklist (engineering)

- [ ] `.env.example`
- [ ] Expanded `.gitignore`
- [ ] Dockerfile (+ compose)
- [ ] CI workflow
- [ ] Auth dependency enforced
- [ ] Routers wired per Phase 2
- [ ] Tests per TEST_PLAN
- [ ] Demo script
- [ ] App title renamed
- [ ] Junk files removed
