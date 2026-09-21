# AGENT_BRIEF — phased work plan

**Repo to modify:** https://github.com/vikaspal1704/recruiter-backend  
**Docs pack location (this folder):** copy/merge these docs into the app repo as needed; do not treat docs-only folder as the runtime app.

**Rule:** Prefer additive polish. Do **not** delete working upload/parse/search without cause. Strip secrets; never commit `.env`.

---

## Phase 1 — Hygiene + README / Docker / CI

**Goal:** Make the repo look and run like a professional portfolio backend.

### Tasks

1. **Rename** FastAPI title from `Lovable AI MVP Backend` → `Recruiter Talent Search API` (or equivalent).
2. Add root `README.md`, `LICENSE` (MIT © 2026 Vikas Pal), `AGENTS.md`, and `docs/*` from this pack (if not already present).
3. Expand `.gitignore`: `.env`, `venv/`, `.venv/`, `__pycache__/`, `*.py[cod]`, `.pytest_cache/`, `.mypy_cache/`, `.idea/`, `.vscode/`, `dist/`, `*.egg-info/`.
4. **Delete from git** (and stop tracking): all `__pycache__/` trees; root `Java.pdf` and `React.pdf` unless moved to a justified small fixture (prefer delete).
5. Remove DEBUG prints of `SUPABASE_URL` / key prefix from `supabase_client.py`.
6. Add `.env.example` per [TRD.md](TRD.md) — placeholders only.
7. Add `Dockerfile` (+ optional `docker-compose.yml`).
8. Add `.github/workflows/ci.yml` (install + pytest with dummy env + docker build).
9. Ensure `requirements.txt` retains pytest; add any tiny missing test deps only if needed.

### Explicit non-goals this phase

- Do not rewrite resume/search business logic.
- Do not delete unwired routers yet (see Phase 2).

### Exit criteria

Acceptance section **A** in [ACCEPTANCE_CRITERIA.md](ACCEPTANCE_CRITERIA.md).

---

## Phase 2 — Wire routers + auth

**Goal:** Auth is real; outreach/profile usable; empty stubs resolved.

### Tasks

1. Consolidate auth in `dependencies.py`; remove duplicate from `app.py` (or thin re-export).
2. Implement `AUTH_MODE` + `API_KEY` / Bearer verification as specified in TRD.
3. Apply `Depends(require_auth)` (or equivalent) to resume + search routers.
4. Fix missing imports in `outreach.py`, `profile.py`, `background.py`.
5. `app.include_router` for `outreach` and `profile` (SHOULD); `background` optional (COULD).
6. Replace `DUMMY_USER_ID` with authenticated principal where sensible; document API-key system user UUID.
7. Tighten CORS via env.
8. Resolve empty `routes/auth.py` and `routes/analytics.py`: **implement minimal** or **delete** and note in MIGRATION_NOTES.
9. Populate `schemas/` from inline models **or** document decision to keep inline and delete empty schema files.
10. Make embedding/supabase init test-safe (lazy / `APP_ENV=test`).

### Guardrails

- Inspect live route paths before changing them ([API_CONTRACT.md](API_CONTRACT.md)).
- Do not break existing response field names for resume/search.
- Do not commit credentials.

### Exit criteria

Acceptance section **B** MUST (+ SHOULD items if time).

---

## Phase 3 — Tests

**Goal:** CI-credible pytest suite with mocks.

### Tasks

1. Create `tests/conftest.py` with TestClient + env + common mocks.
2. Implement P0 cases from [TEST_PLAN.md](TEST_PLAN.md).
3. Add P1 for any routers wired in Phase 2.
4. Ensure `pytest -q` passes without network.

### Exit criteria

Acceptance section **C**.

---

## Phase 4 — Demo script

**Goal:** One-command (or few-step) happy path for interviews.

### Tasks

1. Add `scripts/demo.sh` that:
   - Checks `.env` exists
   - Hits healthcheck
   - Uploads a sample PDF (fixture or arg)
   - Parses resume_id
   - Runs a search query
   - Optionally sends outreach if `DEMO_OUTREACH=1`
2. Document usage in README.
3. Record expected sample output in comments (no secrets).

### Exit criteria

Acceptance section **D**.

---

## Rewrite policy

Rewrite of a module is allowed **only** when:

1. This brief’s current phase calls for it, **and**
2. Justification is written in the PR/commit body (e.g. “embedding_service import creates remote index — lazy-init required for pytest”), **and**
3. Behavior of public API remains compatible per API_CONTRACT.

Otherwise: patch in place.

---

## Suggested order of PRs

1. `chore: hygiene gitignore purge pycache pdfs + env example`  
2. `docs: README LICENSE agents pack`  
3. `ci: dockerfile + github actions`  
4. `feat: enforce auth + cors from env`  
5. `feat: wire outreach and profile routers`  
6. `test: api suite with mocks`  
7. `chore: demo script`

---

## Hand-off checklist for the next agent

- [ ] Which phase is complete?  
- [ ] Any API_CONTRACT deviations?  
- [ ] Any modules deleted? Why?  
- [ ] Are secrets absent from the branch?
