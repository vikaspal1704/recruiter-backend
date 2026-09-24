# routes/search.py
from fastapi import APIRouter, HTTPException, Query

from schemas.search import SearchResult
from services.embedding_service import semantic_search
from supabase_client import fetch_one, supabase

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/", response_model=list[SearchResult])
async def search(q: str = Query(..., min_length=1), k: int = Query(5, ge=1, le=100)):
    """
    1) Create an embedding for the query via OpenAI
    2) Query Pinecone top-k
    3) Fetch each candidate's row from 'candidate_profiles' (skip missing rows)
    4) Return a JSON list of SearchResult
    """
    try:
        matches = semantic_search(q, top_k=k)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Pinecone error: " + str(e))

    results = []
    for m in matches:
        cid = m["metadata"]["candidate_profile_id"]
        data = fetch_one(supabase, "candidate_profiles", "id", cid)
        if not data:
            continue
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
