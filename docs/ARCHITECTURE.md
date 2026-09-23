# ARCHITECTURE — current vs target

## 1. Current architecture (as cloned)

```text
                    ┌─────────────────────────────────────┐
                    │  FastAPI "Lovable AI MVP Backend"   │
                    │  CORS: allow_origins=["*"]          │
                    │  Auth helper: present, UNUSED on    │
                    │  wired routes                       │
                    └──────────────┬──────────────────────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           │                       │                       │
           ▼                       ▼                       ▼
   GET /healthcheck      routes/resume.py          routes/search.py
   (public)              /resume/upload            /search/?q&k
                         /resume/parse/{id}        (no auth)
                         (no auth; DUMMY_USER_ID)
                                   │                       │
           ┌───────────────────────┼───────────────────────┤
           ▼                       ▼                       ▼
   Supabase Storage          OpenAI chat             OpenAI embeddings
   bucket "resumes"          (parse JSON)                  │
           │                       │                       ▼
           ▼                       ▼                 Pinecone index
   table resumes ──parse──► candidate_profiles ◄── query  candidates-mvp
```

### Present on disk but not mounted in `app.py`

```text
routes/outreach.py      → SendGrid + outreach_logs
routes/profile.py       → profiles table
routes/background.py    → stub Checkr-like flow
routes/auth.py          → EMPTY
routes/analytics.py     → EMPTY
schemas/*.py            → ALL EMPTY (models inline in routes)
services/qa_generator.py, analytics_service.py → unused by routes
```

### Critical smells

1. Secret prefix logged in `supabase_client.py` at import  
2. `__pycache__/` and large tutorial PDFs committed  
3. Duplicate `get_current_user` in `app.py` and `dependencies.py`  
4. Unwired routers reference undefined `get_current_user` (missing import)  
5. Import-time Pinecone index creation in `embedding_service.py` (hard on tests)  
6. No README / Docker / CI / `.env.example` / LICENSE in app repo

---

## 2. Target architecture

```text
                 ┌──────────────────────────────────────────┐
                 │  FastAPI "Recruiter Talent Search API"   │
                 │  CORS: explicit origins from env         │
                 │  Auth: X-API-Key OR Bearer (MUST)        │
                 │  Public: /healthcheck (+ /docs in dev)   │
                 └────────────────────┬─────────────────────┘
                                      │
        ┌───────────────┬─────────────┼─────────────┬───────────────┐
        ▼               ▼             ▼             ▼               ▼
   /resume/*       /search/*    /outreach/*   /profile/*    /background/*
   (wired+)        (wired+)     (wire S1)     (wire S2)     (optional C1)
        │               │             │             │               │
        └───────┬───────┴──────┬──────┴──────┬──────┴───────────────┘
                ▼              ▼             ▼
           Supabase      OpenAI API     SendGrid
           (DB+Storage)  (embed+parse)  (email)
                │              │
                │              ▼
                │         Pinecone
                └─────────────┘
```

### Cross-cutting

| Concern | Target |
|---|---|
| Config | `config.py` (env via dotenv, validated at startup); `.env.example` contract |
| Auth | `dependencies.require_auth` on protected routers |
| Schemas | Shared under `schemas/` |
| Tests | Mock Supabase / OpenAI / Pinecone / SendGrid |
| Deploy | Single container behind HTTPS reverse proxy (out of repo) |
| CI | pytest + docker build |

---

## 3. Request flows (target)

### 3.1 Upload → parse → index

```text
Client + Auth
  → POST /resume/upload (PDF multipart)
  → Supabase Storage put + resumes insert (user_id = auth principal)
  → POST /resume/parse/{resume_id}
  → download PDF → PyPDF2 text → OpenAI structured JSON → embed_text
  → candidate_profiles insert → Pinecone upsert → resumes.parsed=true
    (embedding runs before any write, so an OpenAI failure leaves the resume unparsed)
```

### 3.2 Search

```text
Client + Auth
  → GET /search?q=&k=
  → embed query → Pinecone top_k
  → hydrate candidate_profiles rows
  → return SearchResult[]
```

### 3.3 Outreach (SHOULD)

```text
Client + Auth
  → POST /outreach { candidate_id, subject, body }
  → load candidate email
  → SendGrid send
  → outreach_logs insert
```

---

## 4. Trust boundaries

| Zone | Trust |
|---|---|
| Public internet → API | Untrusted; auth required except health |
| API → Supabase service role | **High privilege** — server only |
| API → OpenAI / Pinecone / SendGrid | Server-side keys only |
| Browser | Must never receive service-role key |

---

## 5. Evolution rules

- Prefer extracting services over growing route handlers.
- Side effects (create Pinecone index, PostHog client) should be lazy or behind `if APP_ENV != "test"`.
- Empty router files must not remain ambiguous: implement, wire, or delete with a note in MIGRATION_NOTES.

---

## 6. Diagram legend

- **Done:** resume, search, healthcheck, auth enforcement, outreach, profile, background stub (Phase 1–2)
- **Done:** mocked pytest suite, Docker + CI, `scripts/demo.sh` (Phase 3–4)
- External clients (Supabase, OpenAI, Pinecone, PostHog) are created lazily on first use (`lazy.py`), so importing the app makes no network calls.
