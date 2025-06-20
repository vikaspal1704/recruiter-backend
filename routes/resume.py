# routes/resume.py

from fastapi import APIRouter, File, UploadFile, HTTPException
from supabase_client import supabase
from services.resume_parser import extract_text_from_pdf, parse_resume_text
from services.embedding_service import embed_text, index
from pydantic import BaseModel

router = APIRouter(prefix="/resume", tags=["resume"])

# We dropped the FK earlier, so this can stay as a dummy:
DUMMY_USER_ID = "00000000-0000-0000-0000-000000000000"

class CandidateProfileResponse(BaseModel):
    id: str
    resume_id: str
    name: str
    email: str
    skills: list[str]
    years_experience: float
    education: str
    raw_text: str

@router.post("/upload", response_model=dict)
async def upload_resume(file: UploadFile = File(...)):
    """
    1) Read bytes from uploaded PDF
    2) Upload to Supabase Storage (bucket “resumes”), with upsert="true"
    3) Insert a row into 'resumes' table with user_id=DUMMY_USER_ID
    4) Return { "resume_id": "<uuid>" }
    """
    contents = await file.read()
    file_key = f"{DUMMY_USER_ID}/{file.filename}"
    supabase.storage.from_("resumes").upload(file_key, contents, {"upsert": "true"})
    file_url: str = supabase.storage.from_("resumes").get_public_url(file_key)

    insert = supabase.table("resumes").insert({
        "user_id": DUMMY_USER_ID,
        "file_url": file_url
    }).execute()

    # .execute() raised if it failed, otherwise .data contains the inserted row
    return { "resume_id": insert.data[0]["id"] }

@router.post("/parse/{resume_id}", response_model=CandidateProfileResponse)
async def parse_resume(resume_id: str):
    """
    1) Fetch the row in 'resumes'
    2) If already parsed, return that candidate_profile
    3) Otherwise, download the PDF, extract text, call OpenAI to parse JSON
    4) Insert into 'candidate_profiles', mark resume as parsed
    5) Generate embedding & upsert into Pinecone
    6) Return the inserted candidate_profile
    """
    r = supabase.table("resumes").select("*").eq("id", resume_id).single().execute()
    if not r.data:
        raise HTTPException(status_code=404, detail="Resume not found")
    resume_row = r.data

    if resume_row.get("parsed", False):
        cp = supabase.table("candidate_profiles").select("*").eq("resume_id", resume_id).single().execute()
        return cp.data  # .data contains the existing candidate

    raw_text = extract_text_from_pdf(resume_row["file_url"])
    parsed = parse_resume_text(raw_text)

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

    supabase.table("resumes").update({"parsed": True}).eq("id", resume_id).execute()

    vect = embed_text(raw_text)
    index.upsert([ (candidate["id"], vect, {"candidate_profile_id": candidate["id"]}) ])

    return candidate
