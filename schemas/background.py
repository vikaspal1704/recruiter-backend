# schemas/background.py
from pydantic import BaseModel


class BackgroundResult(BaseModel):
    status: str
    report_url: str
