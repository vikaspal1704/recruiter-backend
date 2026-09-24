# services/analytics_service.py
"""Optional PostHog tracking; a no-op unless POSTHOG_API_KEY is set."""

import os

from posthog import Posthog

_posthog: Posthog | None = None


def _client() -> Posthog | None:
    global _posthog
    api_key = os.getenv("POSTHOG_API_KEY")
    if not api_key:
        return None
    if _posthog is None:
        _posthog = Posthog(api_key, host=os.getenv("POSTHOG_HOST"))
    return _posthog


def track_event(user_id: str, event: str, properties: dict):
    client = _client()
    if client is None:
        return
    client.capture(
        distinct_id=user_id,
        event=event,
        properties=properties
    )
