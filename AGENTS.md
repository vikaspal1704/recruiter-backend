# AGENTS.md — coding-agent operating guide

This file tells coding agents how to harden **recruiter-backend** without inventing a greenfield app.

**Canonical product name:** Recruiter / talent-search API  
**Repo:** https://github.com/vikaspal1704/recruiter-backend  
**Author:** Vikas Pal

---

## North star

Polish the **existing** FastAPI backend into a hire-ready portfolio demo:

- Resume ingest + parse (Supabase Storage + OpenAI)
- Embedding search (OpenAI embeddings + Pinecone `candidates-mvp`)
- Optional outreach (SendGrid)
- Real docs, Docker, CI, `.env.example`, tests, and **required auth** (API key or Bearer)

Do **not** delete working upload/parse/search behavior without cause.

---

## Before you change anything

1. Read [docs/AGENT_BRIEF.md](docs/AGENT_BRIEF.md) and execute the current phase only.
2. Read [docs/MIGRATION_NOTES.md](docs/MIGRATION_NOTES.md) (keep / delete / rename).
3. **Inspect live route files** under `routes/` before changing paths or response shapes — see [docs/API_CONTRACT.md](docs/API_CONTRACT.md).
4. Confirm what is wired in `app.py` vs what only exists as a file.

### Ground truth snapshot (as of docs pack)

| Item | Reality |
|---|---|
| App title in code | `"Lovable AI MVP Backend"` → **rename** |
| Wired routers | `resume`, `search` only |
| Unwired (have code) | `background`, `outreach`, `profile` |
| Empty stubs | `routes/auth.py`, `routes/analytics.py`, all `schemas/*.py` (0 bytes) |
| Auth | Helpers exist; resume/search **unauthenticated**; unwired routes reference `get_current_user` **without importing it** |
| Health | `GET /healthcheck` |
| Junk in repo | `Java.pdf`, `React.pdf`, `__pycache__/` trees |
| `.gitignore` | Only `.env` and `venv` — **inadequate** |
| README / Docker / CI / tests / LICENSE / `.env.example` | Missing in app repo (this docs pack supplies the plan) |

---

## Hard rules

1. **No secrets in git.** Never commit `.env`, API keys, service-role keys, or debug prints that leak key prefixes.
2. **No `__pycache__` / `*.pyc`.** Expand `.gitignore`; delete committed bytecode.
3. **No unrelated large PDFs** unless justified as fixtures under `tests/fixtures/` (prefer small sample PDFs).
4. **Additive polish > rewrite.** Rewrite only if AGENT_BRIEF phase explicitly justifies it.
5. **Preserve integration pattern:** Supabase + Pinecone + OpenAI (+ SendGrid for outreach). Replace providers only with documented justification.
6. **Auth is MUST** for portfolio quality — even if currently bypassed. Implement API key **or** Bearer (Supabase JWT); protect mutating and PII-returning routes.
7. **Do not invent new public path prefixes** without updating `docs/API_CONTRACT.md` and OpenAPI.
8. **Strip secrets from logs.** Remove `supabase_client.py` DEBUG prints of env values.
9. Prefer fixing empty `schemas/` with real Pydantic models shared by routes (schemas today are empty; models live inline in route files).

---

## Preferred workflow

```text
phase N from AGENT_BRIEF
  → small PR / commit group
  → tests green for that phase
  → update docs if API or env contract changed
```

Suggested commit style: `chore:`, `feat:`, `fix:`, `docs:`, `test:`, `ci:`.

---

## What “done” means

See [docs/ACCEPTANCE_CRITERIA.md](docs/ACCEPTANCE_CRITERIA.md). At minimum for a demo:

- Health works
- Auth rejects missing/invalid credentials
- Upload → parse → search demo script succeeds with mocked or sandbox backends
- Docker build + `pytest` in CI
- README is honest about MVP status

---

## Out of scope for agents (unless PRD/COULD later)

- Full multi-tenant SaaS billing
- Real Checkr / background-check vendor (keep stub unless asked)
- Frontend UI (this is API-only)
- Renaming the GitHub repo (optional; product title rename in FastAPI is required)
