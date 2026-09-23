# schemas/outreach.py
from pydantic import BaseModel


class OutreachPayload(BaseModel):
    candidate_id: str
    subject: str
    body: str  # HTML allowed (sent as SendGrid html_content)


class OutreachResponse(BaseModel):
    status: str
    to: str
