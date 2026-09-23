# Recruiter Backend

**Hire-ready talent-search API** — resume ingest + parse, embedding search (Pinecone), optional outreach email.

> **Status:** MVP portfolio backend, hardened. Upload → parse → search works end to end; every route except `/healthcheck` requires auth (API key or Supabase Bearer); outreach, profile and a background-check **stub** are wired; tests run fully mocked in CI with a Docker build. It is still an MVP, not a full ATS or production SaaS.

**Author:** Vikas Pal · fintech SWE portfolio / job-hunt tooling  
**Repo:** https://github.com/vikaspal1704/recruiter-backend  
**License:** MIT © 2026 Vikas Pal

---

## What it does

| Capability | Endpoint | Notes |
|---|---|---|
| Health | `GET /healthcheck` | Public |
| Resume upload (PDF → Supabase Storage + `resumes` row) | `POST /resume/upload` | Protected; `user_id` = auth principal; 400 non-PDF, 413 too large |
| Resume parse (OpenAI JSON extract → `candidate_profiles` + Pinecone upsert) | `POST /resume/parse/{resume_id}` | Protected; idempotent once parsed |
| Semantic candidate search | `GET /search/?q=…&k=5` | Protected (Pinecone + Supabase) |
| Outreach email (SendGrid) | `POST /outreach/` | Protected; logs to `outreach_logs` |
| Profile get / update | `GET` / `PUT /profile/` | Protected; per authenticated user |
| Background check | `POST /background/run/{candidate_id}` | Protected; **stub** — always “passed”, no vendor called |

Stack: **FastAPI · Supabase · Pinecone · OpenAI · SendGrid · PyPDF2 · pytest** (listed in `requirements.txt`).

### Auth

| `AUTH_MODE` | Accepts |
|---|---|
| `api_key_or_bearer` (default) | `X-API-Key: <API_KEY>` **or** `Authorization: Bearer <Supabase access token>` |
| `api_key` | `X-API-Key` only |
| `bearer` | Supabase Bearer only |
| `off` | Anything — local emergency only; refused when `APP_ENV=production` |

Requests authenticated by API key act as the system user `API_KEY_USER_ID` (default `00000000-0000-0000-0000-000000000000`, matching the rows the MVP already wrote). Bearer requests act as the Supabase user. Missing or invalid credentials → `401`.

---

## Quick start (local)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill secrets locally — never commit .env
uvicorn app:app --reload --host 0.0.0.0 --port 8000
curl http://localhost:8000/healthcheck
```

OpenAPI docs: `http://localhost:8000/docs` (disabled when `APP_ENV=production`).

### Docker

```bash
cp .env.example .env   # fill in
docker compose up --build
# or: docker build -t recruiter-backend . && docker run --env-file .env -p 8000:8000 recruiter-backend
```

### Tests

```bash
pytest -q
```

Tests need no network or real keys: `tests/conftest.py` sets dummy env vars and swaps Supabase and Pinecone for in-memory fakes (`tests/fakes.py`); OpenAI and SendGrid calls are monkeypatched. CI (`.github/workflows/ci.yml`) runs the suite, a secret-hygiene check, and a Docker build + `/healthcheck` smoke test.

### Configuration

All settings come from the environment; see [`.env.example`](.env.example). Required for the core path: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `OPENAI_API_KEY`, `PINECONE_API_KEY`, `PINECONE_ENVIRONMENT`, and `API_KEY` (or Bearer auth). Outreach additionally needs `SENDGRID_API_KEY` and `SENDGRID_FROM_EMAIL`. External clients are created lazily on first use, so a missing key fails that request with a clear error rather than crashing startup.

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

- Auth is enforced on every route except `/healthcheck` (single implementation in `dependencies.py`); API keys are compared in constant time.
- CORS origins come from `CORS_ALLOW_ORIGINS`; `*` is refused when `APP_ENV=production`.
- The server uses the Supabase **service-role** key (bypasses row-level security): keep it server-side only.
- No secrets are logged. If keys were ever printed or committed by the earlier MVP, rotate them.
- Uploads are limited to PDFs up to `MAX_UPLOAD_MB` (default 10); stored filenames are stripped of any path.

---

## Demo flow (happy path)

With a server running against real services and `.env` filled in:

```bash
scripts/demo.sh                      # uses tests/fixtures/sample_resume.pdf
scripts/demo.sh path/to/resume.pdf   # or your own PDF
DEMO_OUTREACH=1 scripts/demo.sh      # also emails the parsed candidate address (use an inbox you control)
```

The script:

1. `GET /healthcheck`
2. `POST /resume/upload` with the PDF → `{ "resume_id": "…" }`
3. `POST /resume/parse/{resume_id}` → candidate profile JSON + Pinecone vector
4. `GET /search/?q=python%20fastapi&k=5` → ranked candidates
5. (optional) `POST /outreach/` → SendGrid email + `outreach_logs` row

It exits with a clear error if `.env` is missing. It authenticates with `API_KEY` from `.env`, so `AUTH_MODE` must be `api_key` or `api_key_or_bearer`.

---

## Contributing / agents

Prefer **additive polish** over rewrite. Follow [AGENTS.md](AGENTS.md) and [docs/AGENT_BRIEF.md](docs/AGENT_BRIEF.md). Inspect live route files before changing paths.
