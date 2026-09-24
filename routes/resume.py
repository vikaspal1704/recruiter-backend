# routes/resume.py

import logging
import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from config import Settings, get_settings
from dependencies import get_current_user
from schemas.resume import CandidateProfileResponse, ResumeUploadResponse
from services.embedding_service import embed_text, index
from services.resume_parser import extract_text_from_pdf, parse_resume_text
from supabase_client import fetch_one, supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resume", tags=["resume"])

PDF_MAGIC = b"%PDF-"


def _safe_filename(filename: str | None) -> str:
    name = os.path.basename((filename or "").replace("\\", "/")).strip()
    return name or "resume.pdf"


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    """
    1) Read bytes from uploaded PDF (400 if not a PDF, 413 if too large)
    2) Upload to Supabase Storage (bucket “resumes”) at {user_id}/{filename}, upsert
    3) Insert a row into 'resumes' table for the authenticated principal
    4) Return { "resume_id": "<uuid>" }
    """
    contents = await file.read(settings.max_upload_bytes + 1)
    if len(contents) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File too large")
    if not contents.startswith(PDF_MAGIC):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    user_id = user["id"]
    file_key = f"{user_id}/{_safe_filename(file.filename)}"
    try:
        supabase.storage.from_("resumes").upload(
            file_key, contents, {"upsert": "true", "content-type": "application/pdf"}
        )
        file_url: str = supabase.storage.from_("resumes").get_public_url(file_key)
        insert = supabase.table("resumes").insert({
            "user_id": user_id,
            "file_url": file_url
        }).execute()
    except Exception:
        logger.exception("resume upload failed for %s", file_key)
        raise HTTPException(status_code=500, detail="Resume upload failed")

    return {"resume_id": insert.data[0]["id"]}


@router.post("/parse/{resume_id}", response_model=CandidateProfileResponse)
async def parse_resume(resume_id: str):
    """
    1) Fetch the row in 'resumes' (404 if missing)
    2) If already parsed, return that candidate_profile
    3) Otherwise, download the PDF, extract text, call OpenAI to parse JSON
    4) Embed the text (before any writes, so a failure leaves nothing half-done)
    5) Insert into 'candidate_profiles', upsert into Pinecone, mark resume as parsed
    6) Return the inserted candidate_profile
    """
    resume_row = fetch_one(supabase, "resumes", "id", resume_id)
    if not resume_row:
        raise HTTPException(status_code=404, detail="Resume not found")

    if resume_row.get("parsed", False):
        existing = fetch_one(supabase, "candidate_profiles", "resume_id", resume_id)
        if existing:
            return existing
        # Marked parsed but the profile is missing: fall through and parse again.

    try:
        raw_text = extract_text_from_pdf(resume_row["file_url"])
        parsed = parse_resume_text(raw_text)
        vect = embed_text(raw_text)
    except Exception as e:
        logger.exception("resume parse failed for %s", resume_id)
        raise HTTPException(status_code=500, detail=f"Resume parse failed: {e}")

    insert = supabase.table("candidate_profiles").insert({
        "resume_id": resume_id,
        "name": parsed["name"],
        "email": parsed["email"],
        "skills": parsed["skills"],
        "years_experience": parsed["years_experience"],
        "education": parsed["education"],
        "raw_text": raw_text
    }).execute()
    candidate = insert.data[0]

    index.upsert([(candidate["id"], vect, {"candidate_profile_id": candidate["id"]})])
    supabase.table("resumes").update({"parsed": True}).eq("id", resume_id).execute()

    return candidate
