# schemas/search.py
from pydantic import BaseModel


class SearchResult(BaseModel):
    candidate_id: str
    name: str
    email: str
    skills: list[str]
    years_experience: float
    education: str
    score: float
