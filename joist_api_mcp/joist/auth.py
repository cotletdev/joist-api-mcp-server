"""Who is signed in: Joist's own answer for the user (`/v7/{user_id}/users`), for "Signed in as ..."."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from joist_api_mcp.core.errors import AuthExpiredError
from joist_api_mcp.joist.client import auth_token, headers, user_url

if TYPE_CHECKING:
    from joist_api_mcp.core.context import ToolContext


async def whoami(ctx: ToolContext) -> str | None:
    """None only when Joist says signed out; any other failure raises (detection tries again later)."""
    if auth_token(ctx) is None:
        return None
    try:
        response = await ctx.call("GET", user_url(ctx), headers=headers(ctx))
    except AuthExpiredError:
        return None
    user: dict[str, Any] = response.json().get("user") or {}
    name = " ".join(part for part in (user.get("first_name"), user.get("last_name")) if part)
    return name or user.get("email") or None
