# routes/outreach.py
from fastapi import APIRouter, Depends, HTTPException
from supabase_client import supabase
from services.email_service import send_email
from pydantic import BaseModel

router = APIRouter(prefix="/outreach", tags=["outreach"])

class OutreachPayload(BaseModel):
    candidate_id: str
    subject: str
    body: str

@router.post("/", response_model=dict)
async def send_outreach(payload: OutreachPayload, user=Depends(get_current_user)):
    # 1. Verify candidate exists
    resp = supabase.from_("candidate_profiles").select("*").eq("id", payload.candidate_id).single().execute()
    data, error = resp.data, resp.error
    if error or not data:
        raise HTTPException(status_code=404, detail="Candidate not found")
    to_email = data["email"]

    # 2. Send email
    status_code, response_body = send_email(to_email, payload.subject, payload.body)
    if status_code not in (200, 202):
        raise HTTPException(status_code=500, detail="Email send failed")

    # 3. Log outreach
    supabase.from_("outreach_logs").insert({
        "candidate_id": payload.candidate_id,
        "sent_by": user["id"],
        "channel": "email",
        "content": payload.body
    }).execute()

    return {"status": "sent", "to": to_email}
