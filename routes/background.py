# routes/background.py
"""STUB: background checks always return "passed" with a placeholder report URL."""

from fastapi import APIRouter, HTTPException

from schemas.background import BackgroundResult
from services.background_check_service import run_background_check
from supabase_client import fetch_one, supabase

router = APIRouter(prefix="/background", tags=["background"])


@router.post(
    "/run/{candidate_id}",
    response_model=BackgroundResult,
    description="Stub: no real vendor is called; always returns a passed placeholder report.",
)
async def run_check(candidate_id: str):
    # 1. Verify candidate exists
    if not fetch_one(supabase, "candidate_profiles", "id", candidate_id):
        raise HTTPException(status_code=404, detail="Candidate not found")

    # 2. Insert “pending” row in background_checks
    ins = supabase.from_("background_checks").insert({
        "candidate_id": candidate_id,
        "status": "pending"
    }).execute()
    # 3. Call stub
    result = run_background_check(candidate_id)
    supabase.from_("background_checks")\
        .update({"status": result["status"], "report_url": result["report_url"]})\
        .eq("id", ins.data[0]["id"]).execute()
    return result
