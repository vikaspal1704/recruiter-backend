# routes/profile.py
from fastapi import APIRouter, Depends, HTTPException
from supabase_client import supabase
from supabase_client import supabase
from supabase_client import supabase
from pydantic import BaseModel

router = APIRouter(prefix="/profile", tags=["profile"])

class ProfileUpdate(BaseModel):
    full_name: str | None
    current_title: str | None
    location: str | None

@router.get("/", response_model=dict)
async def get_profile(user=Depends(get_current_user)):
    user_id = user["id"]
    resp = supabase.from_("profiles").select("*").eq("id", user_id).single().execute()
    data, error = resp.data, resp.error
    if error and hasattr(error, "code") and error.code == "PGRST116":
        # no row → create blank
        insert = supabase.from_("profiles").insert({"id": user_id, "email": user["email"]}).execute()
        data = insert.data[0]
    elif error:
        raise HTTPException(status_code=500, detail=error.message)
    return data

@router.put("/", response_model=dict)
async def update_profile(payload: ProfileUpdate, user=Depends(get_current_user)):
    user_id = user["id"]
    updates = payload.dict(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided")
    resp = supabase.from_("profiles").update(updates).eq("id", user_id).execute()
    data, error = resp.data, resp.error
    if error:
        raise HTTPException(status_code=500, detail=error.message)
    return data[0]
