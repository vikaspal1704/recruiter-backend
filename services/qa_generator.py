# services/qa_generator.py
from openai import OpenAI
import os
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_pre_screen_questions(skills: list[str], years: float):
    prompt = f"""
    You are an AI that writes technical pre-screen questions for candidates.
    Candidate skills: {', '.join(skills)}. Years of experience: {years}.
    Return 5 JSON objects in the format:
    {{
      "question": "<text>",
      "type": "technical" | "behavioral",
      "expected_keywords": ["...", "..."]
    }}
    """
    resp = openai.chat.completions.create(
        model="gpt-4",
        messages=[
           {"role": "system", "content": "You are a JSON‐only question generator."},
           {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    import json
    return json.loads(resp.choices[0].message.content)
