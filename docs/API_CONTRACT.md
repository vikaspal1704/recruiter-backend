# API_CONTRACT — intended public HTTP API

> **Agent rule:** Inspect live files under `routes/` and `app.py` before changing paths or payloads. This contract describes the **intended** public surface based on existing code, with minimal expansion for portfolio quality (auth headers, error shape).

**Base URL (local):** `http://localhost:8000`  
**OpenAPI:** `/docs` (Swagger UI), `/redoc`

---

## 0. Conventions

### Auth (MUST for polished service)

| Header | When |
|---|---|
| `X-API-Key: <API_KEY>` | Demo / simple clients |
| `Authorization: Bearer <supabase_access_token>` | Supabase Auth path |

Health is public. All routes below marked **Protected** require one valid mechanism (per `AUTH_MODE`); missing/invalid → `401` `{"detail": "Missing or invalid credentials"}`. API-key requests act as `API_KEY_USER_ID`; Bearer requests act as the Supabase user.

### Error shape (target)

```json
{ "detail": "human-readable message" }
```

FastAPI default is acceptable; do not invent a second envelope unless refactoring all routes.

### Content types

- JSON: `application/json`
- Upload: `multipart/form-data` field name `file`

---

## 1. Health

### `GET /healthcheck`

- **Auth:** Public  
- **Response `200`:**

```json
{ "status": "ok" }
```

- **Implemented** (additive; existing clients reading `status` are unaffected):

```json
{ "status": "ok", "version": "0.1.0" }
```

---

## 2. Resume (`routes/resume.py`, prefix `/resume`)

### `POST /resume/upload` — Protected

- **Body:** multipart file (`file`), PDF expected  
- **Behavior:** upload to Supabase Storage bucket `resumes` at `{user_id}/{filename}` (filename stripped of any path), insert `resumes` row, return id  
- **`user_id`:** the authenticated principal — Supabase user id for Bearer, `API_KEY_USER_ID` (default `00000000-0000-0000-0000-000000000000`) for API key

**Response `200`:**

```json
{ "resume_id": "<uuid>" }
```

**Errors:** `401` unauthenticated; `422` no `file` field; `400` not a PDF; `413` larger than `MAX_UPLOAD_MB`; `500` storage/DB failure

### `POST /resume/parse/{resume_id}` — Protected

- **Path param:** `resume_id` (uuid)  
- **Behavior:** if already parsed, return existing `candidate_profiles` row; else download PDF, OpenAI parse, embed, insert profile, Pinecone upsert, mark parsed (a parse/embed failure leaves the resume unparsed so it can be retried)

**Response `200` — `CandidateProfileResponse`:**

```json
{
  "id": "<uuid>",
  "resume_id": "<uuid>",
  "name": "string",
  "email": "string",
  "skills": ["string"],
  "years_experience": 0.0,
  "education": "string",
  "raw_text": "string"
}
```

**Errors:** `404` resume not found; `401`; `500` parse/embed failure

---

## 3. Search (`routes/search.py`, prefix `/search`)

### `GET /search/` — Protected

> Note trailing path: router mounts at `/search` and route is `/`, so path is `/search/` (FastAPI may redirect `/search`). **Do not rename** without updating clients and this doc. Inspect `routes/search.py` first.

**Query params:**

| Param | Type | Default | Required |
|---|---|---|---|
| `q` | string (non-empty) | — | yes |
| `k` | int, 1–100 | `5` | no |

**Response `200`:** array of `SearchResult`

```json
[
  {
    "candidate_id": "<uuid>",
    "name": "string",
    "email": "string",
    "skills": ["string"],
    "years_experience": 0.0,
    "education": "string",
    "score": 0.0
  }
]
```

**Errors:** `401`; `422` missing `q` or `k` out of range; `500` with detail prefix `Pinecone error: …`. Matches whose profile row no longer exists are skipped.

---

## 4. Outreach (`routes/outreach.py`, prefix `/outreach`)

### `POST /outreach/` — Protected

**Body:**

```json
{
  "candidate_id": "<uuid>",
  "subject": "string",
  "body": "string (html ok per SendGrid helper)"
}
```

**Response `200`:**

```json
{ "status": "sent", "to": "candidate@email" }
```

**Errors:** `404` candidate not found; `500` `Email send failed` (SendGrid non-2xx or error; nothing is logged); `401`

---

## 5. Profile (`routes/profile.py`, prefix `/profile`)

### `GET /profile/` — Protected

- Loads `profiles` for the principal id; creates a blank row (`id`, `email`) if missing

**Response `200`:** profile row object (Supabase shape)

### `PUT /profile/` — Protected

**Body (`ProfileUpdate`):**

```json
{
  "full_name": "string | null",
  "current_title": "string | null",
  "location": "string | null"
}
```

All fields optional; only fields sent are updated.

**Errors:** `400` no fields; `404` no profile row yet (call `GET /profile/` first); `401`

---

## 6. Background (`routes/background.py`, prefix `/background`)

### `POST /background/run/{candidate_id}` — Protected (stub)

**Response `200`:**

```json
{
  "status": "passed",
  "report_url": "https://example.com/fake-report.pdf"
}
```

**Stub:** no vendor is called; always returns `passed` with a placeholder URL (documented in README and the OpenAPI description). `404` if the candidate does not exist.

---

## 7. Auth / analytics routers

The empty `routes/auth.py` and `routes/analytics.py` stubs were **deleted** (see MIGRATION_NOTES §10). No auth or analytics paths are exposed: authentication is a dependency (`dependencies.require_auth`) applied to every router, and `services/analytics_service.track_event` stays an optional, no-op-without-key service helper.

---

## 8. Endpoints intentionally not expanded

Do not add CRUD-for-everything. Prefer:

- Upload / parse / search / outreach / profile / health

Any new path requires PRD update + this file + tests.

---

## 9. OpenAPI title / tags

| Today | Target |
|---|---|
| FastAPI `title="Lovable AI MVP Backend"` | `Recruiter Talent Search API` (done; override with `APP_TITLE`) |
| Tags | `resume`, `search`, `outreach`, `profile`, `background`, `health` (done) |

---

## 10. Compatibility promise

- Keep existing JSON field names for resume upload/parse and search results unless a versioned `/v1` split is introduced (out of scope unless justified in AGENT_BRIEF).
- Agents must grep `app.include_router` and route decorators before renaming.
