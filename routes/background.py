# routes/background.py
from fastapi import APIRouter, Depends, HTTPException
from supabase_client import supabase
from services.background_check_service import run_background_check
from pydantic import BaseModel

router = APIRouter(prefix="/background", tags=["background"])

class BackgroundResult(BaseModel):
    status: str
    report_url: str

@router.post("/run/{candidate_id}", response_model=BackgroundResult)
async def run_check(candidate_id: str, user=Depends(get_current_user)):
    # 1. Verify candidate exists
    resp = supabase.from_("candidate_profiles").select("*").eq("id", candidate_id).single().execute()
    data, error = resp.data, resp.error
    if error or not data:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # 2. Insert “pending” row in background_checks
    ins = supabase.from_("background_checks").insert({
        "candidate_id": candidate_id,
        "status": "pending"
    }).execute()
    if ins.error:
        raise HTTPException(status_code=500, detail=ins.error.message)
    # 3. Call stub
    result = run_background_check(candidate_id)
    supabase.from_("background_checks")\
        .update({"status": result["status"], "report_url": result["report_url"]})\
        .eq("id", ins.data[0]["id"]).execute()
    return result
