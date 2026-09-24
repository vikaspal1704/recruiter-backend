# services/embedding_service.py

import os

from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

from lazy import LazyProxy
from openai_client import EMBEDDING_MODEL, openai

load_dotenv()

INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "candidates-mvp")
EMBEDDING_DIMENSION = 1536  # text-embedding-ada-002


def _create_index():
    api_key = os.getenv("PINECONE_API_KEY")
    region = os.getenv("PINECONE_ENVIRONMENT")  # e.g. "us-east-1"
    if not (api_key and region):
        raise RuntimeError("Missing PINECONE_API_KEY or PINECONE_ENVIRONMENT in environment")

    pc = Pinecone(api_key=api_key)
    # Ensure the index exists (first use only, never at import time)
    if INDEX_NAME not in pc.list_indexes().names():
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region=region),
        )
    return pc.Index(INDEX_NAME)


# Connected on first use so importing the app makes no network calls.
index = LazyProxy(_create_index)


def embed_text(text: str) -> list[float]:
    resp = openai.embeddings.create(input=text, model=EMBEDDING_MODEL)
    return resp.data[0].embedding


def semantic_search(query: str, top_k: int = 5):
    vec = embed_text(query)
    resp = index.query(vector=vec, top_k=top_k, include_metadata=True)
    return resp["matches"]
