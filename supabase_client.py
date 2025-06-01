# supabase_client.py

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env
load_dotenv()

print("→ DEBUG: SUPABASE_URL =", os.getenv("SUPABASE_URL"))
print("→ DEBUG: SUPABASE_SERVICE_KEY =", os.getenv("SUPABASE_SERVICE_KEY")[:10] + "...")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")

# Initialize Supabase client with the service role key
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
