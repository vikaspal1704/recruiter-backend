# app.py

import os
from fastapi import FastAPI, Depends, HTTPException, Header, status
from supabase_client import supabase
from routes.resume import router as resume_router
from routes.search import router as search_router
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load .env
load_dotenv()

app = FastAPI(title="Lovable AI MVP Backend")

# ---- Auth Middleware (unused when bypassing, but kept if you re-enable auth) ----
async def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid auth header"
        )
    token = authorization.split("Bearer ")[1]
    res = supabase.auth.get_user(token)
    user = res.get("data", {}).get("user")
    if not user or res.get("error"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    return user

# ---- CORS Middleware (adjust origins as needed) ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Include Routers ----
app.include_router(resume_router)
app.include_router(search_router)

@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}

# If you ever want to run via `python app.py`, uncomment below:
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
