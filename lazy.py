# lazy.py
"""Defer creating external clients (Supabase, OpenAI, Pinecone) until first use.

Importing the app must not require live credentials or make network calls, so
tests can run with dummy env vars and mocked clients.
"""

from collections.abc import Callable
from typing import Any


class LazyProxy:
    """Stands in for the object ``factory()`` returns, creating it on first attribute access."""

    def __init__(self, factory: Callable[[], Any]) -> None:
        object.__setattr__(self, "_factory", factory)
        object.__setattr__(self, "_instance", None)

    def _get(self) -> Any:
        if self._instance is None:
            object.__setattr__(self, "_instance", self._factory())
        return self._instance

    def __getattr__(self, name: str) -> Any:
        return getattr(self._get(), name)
