# Recruiter Backend

**Hire-ready talent-search API** — resume ingest + parse, embedding search (Pinecone), optional outreach email.

> **Status:** MVP / portfolio polish in progress. Core upload → parse → search path works; auth is currently bypassed; several routers exist as files but are not wired into `app.py`. Treat this as a working prototype being hardened for recruiter demos and SWE portfolio review — not production SaaS.

**Author:** Vikas Pal · fintech SWE portfolio / job-hunt tooling  
**Repo:** https://github.com/vikaspal1704/recruiter-backend  
**License:** MIT © 2026 Vikas Pal

---

## What it does

| Capability | Endpoint (today) | Notes |
|---|---|---|
| Health | `GET /healthcheck` | Wired |
| Resume upload (PDF → Supabase Storage + `resumes` row) | `POST /resume/upload` | Wired; uses dummy `user_id` |
| Resume parse (OpenAI JSON extract → `candidate_profiles` + Pinecone upsert) | `POST /resume/parse/{resume_id}` | Wired |
| Semantic candidate search | `GET /search/?q=…&k=5` | Wired (Pinecone + Supabase) |
| Outreach email (SendGrid) | `POST /outreach/` | Code exists; **not included** in `app.py` |
| Profile CRUD | `GET/PUT /profile/` | Code exists; **not included** |
| Background check stub | `POST /background/run/{candidate_id}` | Code exists; **not included** |
| Auth / analytics routers | `routes/auth.py`, `routes/analytics.py` | **Empty files** |

Stack: **FastAPI · Supabase · Pinecone · OpenAI · SendGrid · PyPDF2 · pytest** (listed in `requirements.txt`).

---

## Quick start (local)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill secrets locally — never commit .env
uvicorn app:app --reload --host 0.0.0.0 --port 8000
curl http://localhost:8000/healthcheck
```

OpenAPI docs: `http://localhost:8000/docs`

Docker / CI targets are specified in [docs/TRD.md](docs/TRD.md) and phased in [docs/AGENT_BRIEF.md](docs/AGENT_BRIEF.md). Agents should add them if missing.

---

## Documentation map (agents start here)

| Doc | Purpose |
|---|---|
| [AGENTS.md](AGENTS.md) | How coding agents should work in this repo |
| [docs/AGENT_BRIEF.md](docs/AGENT_BRIEF.md) | Phased build plan (hygiene → auth → tests → demo) |
| [docs/PRD.md](docs/PRD.md) | Product goals, MUST/SHOULD/COULD, non-goals |
| [docs/TRD.md](docs/TRD.md) | Target layout, env contract, Docker, CI |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Current vs target architecture |
| [docs/API_CONTRACT.md](docs/API_CONTRACT.md) | Intended public HTTP API |
| [docs/ACCEPTANCE_CRITERIA.md](docs/ACCEPTANCE_CRITERIA.md) | Done-when checklist |
| [docs/TEST_PLAN.md](docs/TEST_PLAN.md) | Test strategy and cases |
| [docs/MIGRATION_NOTES.md](docs/MIGRATION_NOTES.md) | Keep / delete / rename guidance |

---

## Security notes (honest)

- Auth helpers exist (`dependencies.get_current_user`, duplicate in `app.py`) but **resume/search routes do not require auth**.
- CORS is `allow_origins=["*"]` — tighten for any public deploy.
- `supabase_client.py` currently **prints a prefix of `SUPABASE_SERVICE_KEY` at import** — remove that in hygiene phase.
- Never commit `.env`, `__pycache__/`, credentials, or large unrelated PDFs (`Java.pdf`, `React.pdf` are junk and should be removed).

---

## Demo flow (happy path)

1. `POST /resume/upload` with a PDF → `{ "resume_id": "…" }`
2. `POST /resume/parse/{resume_id}` → candidate profile JSON + Pinecone vector
3. `GET /search/?q=python%20fastapi&k=5` → ranked candidates
4. (After wiring) `POST /outreach/` with API key / Bearer → SendGrid email + log row

---

## Contributing / agents

Prefer **additive polish** over rewrite. Follow [AGENTS.md](AGENTS.md) and [docs/AGENT_BRIEF.md](docs/AGENT_BRIEF.md). Inspect live route files before changing paths.
