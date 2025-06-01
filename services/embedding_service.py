# services/embedding_service.py

import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENVIRONMENT")  # e.g. "us-east-1"
INDEX_NAME = "candidates-mvp"

if not (OPENAI_API_KEY and PINECONE_API_KEY and PINECONE_ENV):
    raise RuntimeError("Missing OPENAI_API_KEY, PINECONE_API_KEY, or PINECONE_ENVIRONMENT in .env")

# Initialize OpenAI
openai = OpenAI(api_key=OPENAI_API_KEY)

# Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)

# Ensure the index exists
existing = pc.list_indexes().names()
if INDEX_NAME not in existing:
    pc.create_index(
        name=INDEX_NAME,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=PINECONE_ENV)
    )

# Connect to the index
index = pc.Index(INDEX_NAME)

def embed_text(text: str) -> list[float]:
    resp = openai.embeddings.create(input=text, model="text-embedding-ada-002")
    return resp["data"][0]["embedding"]

def semantic_search(query: str, top_k: int = 5):
    vec = embed_text(query)
    resp = index.query(vec, top_k=top_k, include_metadata=True)
    return resp["matches"]
