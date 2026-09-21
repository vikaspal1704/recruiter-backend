# TEST_PLAN — recruiter-backend

**Runner:** `pytest` (already in `requirements.txt`; `pytest-mock` available)  
**Principle:** Unit/API tests with **mocks** for Supabase, OpenAI, Pinecone, SendGrid. No paid API calls in CI.

---

## 1. Test environment

Set in CI / `conftest.py`:

```bash
APP_ENV=test
AUTH_MODE=api_key
API_KEY=test-api-key
SUPABASE_URL=https://example.supabase.co
SUPABASE_SERVICE_KEY=test-service-key
OPENAI_API_KEY=test-openai
PINECONE_API_KEY=test-pinecone
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=candidates-mvp
SENDGRID_API_KEY=test-sendgrid
SENDGRID_FROM_EMAIL=noreply@example.com
CORS_ALLOW_ORIGINS=http://localhost:3000
```

### Import hazards to neutralize

| Module | Risk in tests | Mitigation |
|---|---|---|
| `supabase_client.py` | Requires env; prints secrets | Patch/lazy init; remove prints |
| `embedding_service.py` | Creates Pinecone index on import | Lazy client; skip network when `APP_ENV=test` |
| `resume_parser.py` | Requires OpenAI key at import | Allow dummy key; mock client |

Use `fastapi.testclient.TestClient` against `app:app`.

---

## 2. Coverage priorities

| Priority | Area |
|---|---|
| P0 | Health, auth gate, resume upload/parse (mocked), search (mocked) |
| P1 | Outreach send + 404 candidate; profile get/update |
| P2 | Background stub; upload validation; CORS headers |

---

## 3. Cases

### 3.1 Health — P0

| ID | Case | Expect |
|---|---|---|
| H1 | `GET /healthcheck` no auth | `200` `{"status":"ok"}` |

### 3.2 Auth — P0

| ID | Case | Expect |
|---|---|---|
| A1 | `POST /resume/upload` without headers | `401` |
| A2 | `GET /search/?q=python` without headers | `401` |
| A3 | Invalid `X-API-Key` | `401` |
| A4 | Valid `X-API-Key: test-api-key` reaches handler (mocked deps) | not 401 |
| A5 | Invalid Bearer | `401` |
| A6 | Valid Bearer (mock `supabase.auth.get_user`) | not 401 |

### 3.3 Resume — P0

| ID | Case | Expect |
|---|---|---|
| R1 | Upload PDF with auth; mock storage + insert | `200` with `resume_id` |
| R2 | Parse unknown id | `404` |
| R3 | Parse already-parsed resume returns existing profile | `200`, no re-embed |
| R4 | Parse fresh: mock PDF extract + OpenAI JSON + embed upsert | `200` profile fields |
| R5 | Non-file body | `422` |

### 3.4 Search — P0

| ID | Case | Expect |
|---|---|---|
| S1 | Missing `q` | `422` |
| S2 | Mock `semantic_search` + profile fetch | `200` list with `score` |
| S3 | Pinecone exception | `500` detail contains error context |

### 3.5 Outreach — P1 (after wire)

| ID | Case | Expect |
|---|---|---|
| O1 | Candidate missing | `404` |
| O2 | SendGrid returns 202 | `200` `status=sent` |
| O3 | SendGrid failure | `500` |

### 3.6 Profile — P1 (after wire)

| ID | Case | Expect |
|---|---|---|
| P1 | GET creates blank when missing | `200` |
| P2 | PUT empty body | `400` |
| P3 | PUT with fields | `200` updated |

### 3.7 Background — P2 (optional)

| ID | Case | Expect |
|---|---|---|
| B1 | Stub returns passed + report_url | `200` |

---

## 4. Fixtures

- Prefer generating a minimal PDF in-memory (or tiny `tests/fixtures/sample.pdf` &lt; 50KB).
- **Do not** commit `Java.pdf` / `React.pdf` as fixtures.

Example mock patterns:

```python
# illustrative only — agents implement properly
monkeypatch.setattr("routes.resume.supabase", mock_supabase)
monkeypatch.setattr("services.resume_parser.parse_resume_text", lambda t: {...})
monkeypatch.setattr("services.embedding_service.semantic_search", lambda q, top_k=5: [...])
```

---

## 5. What not to test in CI

- Live OpenAI token spend
- Live Pinecone upserts against personal indexes
- Live SendGrid delivery
- Full Supabase schema migrations (document separately if needed)

Optional **manual smoke** checklist (local with real `.env`):

1. Health  
2. Upload real PDF  
3. Parse  
4. Search query matching resume skills  
5. Outreach to a safe inbox you control

---

## 6. Quality gates

| Gate | Command |
|---|---|
| Unit/API | `pytest -q` |
| Docker | `docker build -t recruiter-backend:test .` |
| Secret hygiene | Fail CI if `.env` staged (optional `gitleaks` COULD) |

---

## 7. Tracing failures to modules

| Failure | Likely module |
|---|---|
| Import error on TestClient | `supabase_client` / `embedding_service` side effects |
| 500 on search | `semantic_search` or Supabase hydrate |
| Auth flaky | Duplicate auth functions / AUTH_MODE misconfig |
| Outreach NameError | missing `get_current_user` import |
