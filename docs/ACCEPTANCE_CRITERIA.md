# ACCEPTANCE_CRITERIA — polished recruiter-backend

A phase is “done” only when its criteria below pass. Overall portfolio acceptance requires **all MUST** items.

---

## A. Hygiene & docs (Phase 1) — MUST

| ID | Criterion | Verify |
|---|---|---|
| A1 | App FastAPI title is **not** “Lovable AI MVP Backend” | `grep -n title app.py` |
| A2 | Root README exists, honest MVP status, links to docs | Open README |
| A3 | MIT LICENSE © 2026 Vikas Pal present | File exists |
| A4 | `.env.example` lists required vars with placeholders only | No real keys |
| A5 | `.gitignore` excludes `.env`, `venv/`, `.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, IDE junk | Review file |
| A6 | No `__pycache__` committed | `git ls-files \| grep pycache` empty |
| A7 | `Java.pdf` / `React.pdf` removed (or moved to justified fixtures) | Not at repo root |
| A8 | `supabase_client` does not print secret prefixes | Code review |
| A9 | Dockerfile builds successfully | `docker build .` |
| A10 | CI workflow runs on PR/push | `.github/workflows/ci.yml` |

---

## B. Auth & routers (Phase 2) — MUST / SHOULD

| ID | Criterion | Level | Verify |
|---|---|---|---|
| B1 | Missing auth → `401` on `/resume/upload`, `/resume/parse/{id}`, `/search/` | MUST | pytest / curl |
| B2 | Valid `X-API-Key` or Bearer succeeds on protected routes | MUST | pytest |
| B3 | `/healthcheck` remains usable without auth | MUST | curl |
| B4 | Single auth implementation (no divergent copies) | MUST | code review |
| B5 | `outreach` router included and import-fixed | SHOULD | OpenAPI lists tag |
| B6 | `profile` router included and import-fixed | SHOULD | OpenAPI |
| B7 | CORS origins from env; not `*` in production profile | MUST | config review |
| B8 | Resume upload associates `user_id` with auth principal (or documented API-key system user) | SHOULD | code + doc |
| B9 | Empty `auth.py` / `analytics.py` either implemented or removed with note | MUST | no ambiguous empty public modules left unexplained |

---

## C. Tests (Phase 3) — MUST

| ID | Criterion | Verify |
|---|---|---|
| C1 | `pytest` exits 0 in CI with dummy env | CI log |
| C2 | Health test exists | `tests/test_health.py` |
| C3 | Auth rejection tests exist | `tests/test_auth.py` |
| C4 | Resume upload/parse tested with mocks (no live OpenAI/Supabase required) | tests |
| C5 | Search tested with mocked Pinecone + Supabase | tests |
| C6 | No test writes real emails via SendGrid | code review |

---

## D. Demo (Phase 4) — SHOULD

| ID | Criterion | Verify |
|---|---|---|
| D1 | `scripts/demo.sh` (or Make target) documents/runs happy path | Script exists |
| D2 | Demo fails clearly if `.env` missing | Script behavior |
| D3 | README “Demo flow” matches script | Doc sync |

---

## E. Non-functional — MUST

| ID | Criterion |
|---|---|
| E1 | No credentials in git history of default branch for new commits (rotate if any leaked historically) |
| E2 | Additive changes: upload→parse→search still works when integrations configured |
| E3 | Working features not deleted without MIGRATION_NOTES justification |
| E4 | API paths match API_CONTRACT unless contract updated in same change |

---

## F. Definition of Done (portfolio tag)

Ship-ready for interview demo when **A + B MUST + C + E** pass and README can be followed cold by a recruiter in one sitting.
