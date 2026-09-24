# schemas/profile.py
from pydantic import BaseModel


class ProfileUpdate(BaseModel):
    # Defaults make every field optional so PUT can send a partial update.
    full_name: str | None = None
    current_title: str | None = None
    location: str | None = None
