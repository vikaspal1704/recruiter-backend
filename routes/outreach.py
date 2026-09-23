# routes/outreach.py
import logging

from fastapi import APIRouter, Depends, HTTPException

from dependencies import get_current_user
from schemas.outreach import OutreachPayload, OutreachResponse
from services.email_service import send_email
from supabase_client import fetch_one, supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/outreach", tags=["outreach"])


@router.post("/", response_model=OutreachResponse)
async def send_outreach(payload: OutreachPayload, user: dict = Depends(get_current_user)):
    # 1. Verify candidate exists
    data = fetch_one(supabase, "candidate_profiles", "id", payload.candidate_id)
    if not data:
        raise HTTPException(status_code=404, detail="Candidate not found")
    to_email = data["email"]

    # 2. Send email
    try:
        status_code, _ = send_email(to_email, payload.subject, payload.body)
    except Exception:
        logger.exception("outreach email to candidate %s failed", payload.candidate_id)
        raise HTTPException(status_code=500, detail="Email send failed")
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
