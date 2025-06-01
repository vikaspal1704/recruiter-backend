from fastapi import APIRouter, HTTPException, Query
from services.embedding_service import semantic_search
from supabase_client import supabase
from pydantic import BaseModel

router = APIRouter(prefix="/search", tags=["search"])

class SearchResult(BaseModel):
    candidate_id: str
    name: str
    email: str
    skills: list[str]
    years_experience: float
    education: str
    score: float

@router.get("/", response_model=list[SearchResult])
async def search(q: str = Query(...), k: int = Query(5)):
    """
    1) Create an embedding for the query via OpenAI
    2) Query Pinecone top-k
    3) Fetch each candidate's row from 'candidate_profiles'
    4) Return a JSON list of SearchResult
    """
    try:
        matches = semantic_search(q, top_k=k)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Pinecone error: " + str(e))

    results = []
    for m in matches:
        cid = m["metadata"]["candidate_profile_id"]
        # ---- use .table("candidate_profiles") here ----
        cp = supabase.table("candidate_profiles").select("*").eq("id", cid).single().execute()
        if cp.error or not cp.data:
            continue
        data = cp.data
        results.append({
            "candidate_id": cid,
            "name": data["name"],
            "email": data["email"],
            "skills": data["skills"],
            "years_experience": data["years_experience"],
            "education": data["education"],
            "score": m["score"]
        })

    return results
