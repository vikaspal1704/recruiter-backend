# dependencies.py
import os
from fastapi import Header, HTTPException, status
from supabase_client import supabase

async def get_current_user(authorization: str = Header(...)):
    """
    Expects: Authorization: Bearer <access_token>
    Verifies the token with Supabase Auth and returns the user dict.
    Raises 401 if invalid or missing.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )
    token = authorization.split("Bearer ")[1]
    result = supabase.auth.get_user(token)
    user = result.get("data", {}).get("user")
    if not user or result.get("error"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return user
