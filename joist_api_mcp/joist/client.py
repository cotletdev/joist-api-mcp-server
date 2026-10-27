"""Joist panel requests, recorded 26.10.2026 on pro.joistapp.com.

The panel (a React SPA) calls `https://gateway.prd.joistapp.com/api/v{6..9}/{user_id}/...` as JSON. The session
is the cookie `auth:production` on `.joistapp.com` (name URL-encoded as `auth%3Aproduction`, value
`<user_id>:<token>`), and every call sends `X-Api-Authorization: Joist-Token <user_id>:<token>`. The user id is
also the first path segment of most calls and the cookie `userId:production`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import unquote

from joist_api_mcp.core.errors import AuthExpiredError

if TYPE_CHECKING:
    from joist_api_mcp.core.context import ToolContext

WEB = "https://pro.joistapp.com"
API = "https://gateway.prd.joistapp.com/api"
# 200 with the token header, 401 "Invalid authentication token." without it (checked 26.10.2026; the cookie
# alone is not enough). `/v7/users` without a user id answers 200 to anyone, so it proves nothing.
SESSION_URL = f"{API}/v9/companies.json"
DEV_MIRROR_KEY = "cotlet:dev-auth"
AUTH_COOKIES = ("auth:production", "auth%3Aproduction")


def auth_token(ctx: ToolContext) -> str | None:
    """`<user_id>:<token>` from the auth cookie of the profile, or None when it is not there."""
    for cookie in ctx.profile.cookies:
        if cookie.name in AUTH_COOKIES and cookie.value:
            value = unquote(cookie.value)
            if ":" in value:
                return value
    # A dev run gets no cookie values, only this localStorage mirror of the token.
    mirror = (ctx.profile.local_storage.get(WEB) or {}).get(DEV_MIRROR_KEY, "")
    return mirror if ":" in mirror else None


def user_id(ctx: ToolContext) -> str:
    """The signed-in user's id (first part of the token). Raises `auth_expired` without the cookie."""
    token = auth_token(ctx)
    if token is None:
        raise AuthExpiredError("Joist has no session in this browser. Sign in again in Chrome, then run connect.")
    return token.split(":", 1)[0]


def user_url(ctx: ToolContext) -> str:
    """The signed-in user's record (name, email, company id)."""
    return f"{API}/v7/{user_id(ctx)}/users"


def headers(ctx: ToolContext) -> dict[str, str]:
    """What the panel sends with every API call."""
    token = auth_token(ctx)
    found = {"accept": "application/json", "origin": WEB, "referer": f"{WEB}/"}
    if token is not None:
        found["x-api-authorization"] = f"Joist-Token {token}"
    return found


def request_headers(ctx: ToolContext) -> dict[str, str]:
    """The tools' identity headers for `docker/prod-run … request` (integrations/CLAUDE.md)."""
    return headers(ctx)
