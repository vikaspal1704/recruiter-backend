# services/analytics_service.py
import os
from posthog import Posthog

posthog = Posthog(os.getenv("POSTHOG_API_KEY"), host=os.getenv("POSTHOG_HOST"))

def track_event(user_id: str, event: str, properties: dict):
    posthog.capture(
        distinct_id=user_id,
        event=event,
        properties=properties
    )
