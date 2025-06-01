# services/resume_parser.py

import tempfile, requests, os, json
from PyPDF2 import PdfReader
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY in .env")

openai = OpenAI(api_key=OPENAI_API_KEY)

def extract_text_from_pdf(url: str) -> str:
    # 1) Download the PDF bytes
    r = requests.get(url)
    tf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tf.write(r.content)
    tf.close()

    # 2) Extract text page by page
    reader = PdfReader(tf.name)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    os.unlink(tf.name)
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
        model="gpt-4",
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
