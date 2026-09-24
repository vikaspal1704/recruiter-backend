# services/resume_parser.py

import io
import json

import requests
from PyPDF2 import PdfReader

from openai_client import CHAT_MODEL, openai

DOWNLOAD_TIMEOUT_SEC = 30


def extract_text_from_pdf(url: str) -> str:
    # 1) Download the PDF bytes
    r = requests.get(url, timeout=DOWNLOAD_TIMEOUT_SEC)
    r.raise_for_status()

    # 2) Extract text page by page
    reader = PdfReader(io.BytesIO(r.content))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def parse_resume_text(raw_text: str) -> dict:
    prompt = f"""
Extract the following fields from this resume text. Return JSON ONLY:

{{ 
  "name": "<full name>", 
  "email": "<email>", 
  "skills": ["skill1", "skill2", ...], 
  "years_experience": <number>, 
  "education": "<highest degree and institution>" 
}}

Resume Text:
\"\"\"{raw_text}\"\"\"
"""
    res = openai.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": "You are a JSON responder for parsing resumes."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    try:
        return json.loads(res.choices[0].message.content)
    except Exception as e:
        raise RuntimeError("Failed to parse JSON from OpenAI: " + str(e))
