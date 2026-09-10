from __future__ import annotations

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from .auth_tokens import resolve_token


def rate_limit_key(request: Request) -> str:
    """Rate-limits by authenticated user when possible, falling back to
    client IP for unauthenticated endpoints (login/register). This way a
    single account can't dodge its quota by opening new sessions, and
    unauthenticated brute-force attempts are still capped per IP."""
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
        user_id = resolve_token(token)
        if user_id is not None:
            return f"user:{user_id}"
    return f"ip:{get_remote_address(request)}"


# Generous global default so normal usage never trips it; specific routes
# (auth, anything that calls the OpenAI API) get tighter limits below.
limiter = Limiter(key_func=rate_limit_key, default_limits=["200/minute"])
