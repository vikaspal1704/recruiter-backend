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

Health is public. All routes below marked **Protected** require one valid mechanism (per `AUTH_MODE`).

### Error shape (target)

```json
{ "detail": "human-readable message" }
```

FastAPI default is acceptable; do not invent a second envelope unless refactoring all routes.

### Content types

- JSON: `application/json`
- Upload: `multipart/form-data` field name `file`

---

## 1. Health — wired today

### `GET /healthcheck`

- **Auth:** Public  
- **Response `200`:**

```json
{ "status": "ok" }
```

- **Optional SHOULD extension** (do not break existing clients):

```json
{ "status": "ok", "version": "0.1.0" }
```

---

## 2. Resume — wired today (`routes/resume.py`, prefix `/resume`)

### `POST /resume/upload` — Protected

- **Body:** multipart file (`file`), PDF expected  
- **Behavior (current):** upload to Supabase Storage bucket `resumes` at `{user_id}/{filename}`, insert `resumes` row, return id  
- **Today’s quirk:** `user_id` hardcoded `DUMMY_USER_ID = 00000000-0000-0000-0000-000000000000`  
- **Target:** use authenticated user id (or documented system UUID for API-key mode)

**Response `200`:**

```json
{ "resume_id": "<uuid>" }
```

**Errors:** `401` unauthenticated; `400` missing/non-PDF (SHOULD validate); `413` too large (SHOULD); `500` storage/DB failure

### `POST /resume/parse/{resume_id}` — Protected

- **Path param:** `resume_id` (uuid)  
- **Behavior:** if already parsed, return existing `candidate_profiles` row; else download PDF, OpenAI parse, insert profile, mark parsed, Pinecone upsert

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

## 3. Search — wired today (`routes/search.py`, prefix `/search`)

### `GET /search/` — Protected

> Note trailing path: router mounts at `/search` and route is `/`, so path is `/search/` (FastAPI may redirect `/search`). **Do not rename** without updating clients and this doc. Inspect `routes/search.py` first.

**Query params:**

| Param | Type | Default | Required |
|---|---|---|---|
| `q` | string | — | yes |
| `k` | int | `5` | no |

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

**Errors:** `401`; `500` with detail prefix `Pinecone error: …` (current behavior)

---

## 4. Outreach — exists, not wired (`routes/outreach.py`, prefix `/outreach`)

### `POST /outreach/` — Protected (wire in Phase 2)

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

**Errors:** `404` candidate not found; `500` email send failed; `401`

**Precondition to wire:** `from dependencies import get_current_user` (currently missing).

---

## 5. Profile — exists, not wired (`routes/profile.py`, prefix `/profile`)

### `GET /profile/` — Protected

- Loads `profiles` for `user["id"]`; creates blank row if missing (`PGRST116`)

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

**Errors:** `400` no fields; `500` DB; `401`

**Precondition:** import `get_current_user`; remove triplicate `supabase` imports.

---

## 6. Background — exists, not wired (`routes/background.py`, prefix `/background`)

### `POST /background/run/{candidate_id}` — Protected (COULD)

**Response `200`:**

```json
{
  "status": "passed",
  "report_url": "https://example.com/fake-report.pdf"
}
```

Clearly document as **stub** in README/OpenAPI description.

---

## 7. Auth / analytics routers

| File | Status | Contract action |
|---|---|---|
| `routes/auth.py` | Empty | Do **not** advertise paths until implemented. If implementing: document signup/login against Supabase Auth explicitly. |
| `routes/analytics.py` | Empty | No public API until designed. Prefer service-level tracking from existing routes. |

---

## 8. Endpoints intentionally not expanded

Do not add CRUD-for-everything. Prefer:

- Upload / parse / search / outreach / profile / health

Any new path requires PRD update + this file + tests.

---

## 9. OpenAPI title / tags

| Today | Target |
|---|---|
| FastAPI `title="Lovable AI MVP Backend"` | `Recruiter Talent Search API` (or similar) |
| Tags | `resume`, `search`, add `outreach`, `profile`, `background`, `health` |

---

## 10. Compatibility promise

- Keep existing JSON field names for resume upload/parse and search results unless a versioned `/v1` split is introduced (out of scope unless justified in AGENT_BRIEF).
- Agents must grep `app.include_router` and route decorators before renaming.
