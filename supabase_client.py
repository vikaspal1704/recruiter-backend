# supabase_client.py

import os
from typing import Any

from dotenv import load_dotenv
from supabase import Client, create_client

from lazy import LazyProxy

# Load environment variables from .env
load_dotenv()


def create_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in environment")
    # Service role key: server-side only, bypasses row-level security.
    return create_client(url, key)


# Created on first use so importing the app does not require live credentials.
supabase: Client = LazyProxy(create_supabase_client)  # type: ignore[assignment]


def fetch_one(client: Client, table: str, column: str, value: Any) -> dict | None:
    """Return the first row where ``column == value``, or None if there is none.

    postgrest's ``.single()`` raises when no row matches, and responses have no
    ``.error`` attribute, so "not found" is detected from the returned rows instead.
    """
    resp = client.table(table).select("*").eq(column, value).limit(1).execute()
    return resp.data[0] if resp.data else None
