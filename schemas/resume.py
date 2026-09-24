# schemas/resume.py
from pydantic import BaseModel


class ResumeUploadResponse(BaseModel):
    resume_id: str


class CandidateProfileResponse(BaseModel):
    id: str
    resume_id: str
    name: str
    email: str
    skills: list[str]
    years_experience: float
    education: str
    raw_text: str
