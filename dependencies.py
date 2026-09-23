# dependencies.py
"""Single source of truth for authentication (docs/TRD.md §3).

AUTH_MODE:
  api_key            -> X-API-Key must equal API_KEY
  bearer             -> Authorization: Bearer <Supabase access token>
  api_key_or_bearer  -> either of the above
  off                -> no auth (local emergency only; rejected in production)

Returns a principal dict: {"id": ..., "email": ..., "auth": "api_key" | "bearer" | "off"}.
Requests authenticated with the API key act as API_KEY_USER_ID.
"""

import hmac
import logging

from fastapi import Depends, Header, HTTPException, status
from gotrue.errors import AuthError

from config import Settings, get_settings
from supabase_client import supabase

logger = logging.getLogger(__name__)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _api_key_principal(settings: Settings, x_api_key: str | None) -> dict | None:
    if not x_api_key or not settings.api_key:
        return None
    if not hmac.compare_digest(x_api_key.encode(), settings.api_key.encode()):
        return None
    return {"id": settings.api_key_user_id, "email": None, "auth": "api_key"}


def _bearer_principal(authorization: str | None) -> dict | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    try:
        result = supabase.auth.get_user(token.strip())
    except AuthError:
        return None
    user = result.user if result else None
    if not user:
        return None
    return {"id": str(user.id), "email": user.email, "auth": "bearer"}


async def require_auth(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> dict:
    mode = settings.auth_mode
    if mode == "off":
        return {"id": settings.api_key_user_id, "email": None, "auth": "off"}

    principal = None
    if mode in ("api_key", "api_key_or_bearer"):
        principal = _api_key_principal(settings, x_api_key)
    if principal is None and mode in ("bearer", "api_key_or_bearer"):
        principal = _bearer_principal(authorization)
    if principal is None:
        raise _unauthorized("Missing or invalid credentials")
    return principal


# Routes depend on this name; it is the same dependency as require_auth.
get_current_user = require_auth
