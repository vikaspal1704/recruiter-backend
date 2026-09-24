# openai_client.py
"""Shared, lazily created OpenAI client and model names."""

import os

from dotenv import load_dotenv
from openai import OpenAI

from lazy import LazyProxy

load_dotenv()

CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4")
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")


def _create_openai() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY in environment")
    return OpenAI(api_key=api_key)


openai: OpenAI = LazyProxy(_create_openai)  # type: ignore[assignment]
