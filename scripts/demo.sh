#!/usr/bin/env bash
# Happy-path demo against a running server: health -> upload -> parse -> search
# (-> outreach when DEMO_OUTREACH=1).
#
# Usage:
#   uvicorn app:app --port 8000        # in another terminal, with a real .env
#   scripts/demo.sh [path/to/resume.pdf]
#
# Env overrides:
#   BASE_URL       default http://localhost:8000
#   DEMO_QUERY     default "python fastapi"
#   DEMO_OUTREACH  set to 1 to also POST /outreach/ -- this emails the address parsed
#                  from the resume, so only use a resume whose inbox you control.
#
# Requires AUTH_MODE=api_key or api_key_or_bearer; API_KEY is read from .env.
#
# Expected output (abridged, ids vary):
#   1) Health        {"status":"ok","version":"0.1.0"}
#   2) Upload        resume_id=6f1c...
#   3) Parse         candidate_id=a93e... name=Jane Doe
#   4) Search        [{"candidate_id":"a93e...","name":"Jane Doe",...,"score":0.87}]
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  echo "ERROR: .env not found. Run: cp .env.example .env  and fill in real credentials." >&2
  exit 1
fi

# Read only what we need; .env is not safe to `source` (values may contain spaces).
API_KEY="${API_KEY:-$(grep -E '^API_KEY=' .env | tail -n 1 | cut -d= -f2-)}"
if [[ -z "$API_KEY" ]]; then
  echo "ERROR: API_KEY is empty in .env" >&2
  exit 1
fi

BASE_URL="${BASE_URL:-http://localhost:8000}"
QUERY="${DEMO_QUERY:-python fastapi}"
PDF="${1:-tests/fixtures/sample_resume.pdf}"

if [[ ! -f "$PDF" ]]; then
  echo "ERROR: resume PDF not found: $PDF" >&2
  exit 1
fi

json_field() {
  python3 -c 'import json, sys; print(json.load(sys.stdin)[sys.argv[1]])' "$1"
}

api() {
  curl -sS --fail-with-body -H "X-API-Key: $API_KEY" "$@"
}

echo "1) Health"
curl -sS --fail "$BASE_URL/healthcheck"
echo

echo "2) Upload $PDF"
resume_id="$(api -F "file=@$PDF;type=application/pdf" "$BASE_URL/resume/upload" | json_field resume_id)"
echo "   resume_id=$resume_id"

echo "3) Parse"
profile="$(api -X POST "$BASE_URL/resume/parse/$resume_id")"
candidate_id="$(json_field id <<<"$profile")"
echo "   candidate_id=$candidate_id name=$(json_field name <<<"$profile")"

echo "4) Search q=\"$QUERY\""
api -G "$BASE_URL/search/" --data-urlencode "q=$QUERY" --data-urlencode "k=5"
echo

if [[ "${DEMO_OUTREACH:-0}" == "1" ]]; then
  echo "5) Outreach to candidate $candidate_id"
  api -H "Content-Type: application/json" \
    -d "{\"candidate_id\": \"$candidate_id\", \"subject\": \"Hello from the demo\", \"body\": \"<p>Hi!</p>\"}" \
    "$BASE_URL/outreach/"
  echo
fi

echo "Demo complete."
