# routes/profile.py
from fastapi import APIRouter, Depends, HTTPException

from dependencies import get_current_user
from schemas.profile import ProfileUpdate
from supabase_client import fetch_one, supabase

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/", response_model=dict)
async def get_profile(user: dict = Depends(get_current_user)):
    user_id = user["id"]
    data = fetch_one(supabase, "profiles", "id", user_id)
    if data is None:
        # no row → create blank
        insert = supabase.from_("profiles").insert({"id": user_id, "email": user.get("email")}).execute()
        data = insert.data[0]
    return data


@router.put("/", response_model=dict)
async def update_profile(payload: ProfileUpdate, user: dict = Depends(get_current_user)):
    user_id = user["id"]
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided")
    resp = supabase.from_("profiles").update(updates).eq("id", user_id).execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    return resp.data[0]
