"""Clients (`contacts` in Joist) and saved items: rows as the tools answer them, and page-number paging."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from joist_api_mcp.core.helpers import page_cursor
from joist_api_mcp.joist.tools._api import address_text, call, local_date, number

if TYPE_CHECKING:
    from joist_api_mcp.core.context import ToolContext


def client_row(ctx: ToolContext, contact: dict[str, Any]) -> dict[str, Any]:
    emails = [e.get("value") for e in contact.get("emails") or [] if e.get("value")]
    phones = [p.get("value") for p in contact.get("phone_numbers") or [] if p.get("value")]
    return {
        "client_id": str(contact.get("id")),
        "name": contact.get("name"),
        "email": emails[0] if emails else None,
        "phone": phones[0] if phones else None,
        "address": address_text(contact.get("address")),
        "notes": contact.get("notes") or "",
        "tags": list(contact.get("tag_list") or []),
        "last_payment_on": local_date(ctx, contact.get("last_payment_received_at")),
    }


def item_row(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "item_id": str(item.get("id")),
        "name": item.get("name"),
        "description": item.get("notes") or "",
        "rate": number(item.get("price")),
        "quantity": number(item.get("quantity")) or 1.0,
        "tax_ids": [str(t.get("tax_id") or t.get("id")) for t in item.get("item_taxes") or [] if isinstance(t, dict)],
    }


async def paged(ctx: ToolContext, resource: str, args: dict[str, Any]) -> tuple[list[dict[str, Any]], str | None]:
    """One Joist page of clients or items (page from 1, searched when `search` is set). Joist's page size is
    its own; a page with rows gives the next page as the cursor, an empty one ends the list."""
    page = page_cursor(args.get("cursor"))
    search = str(args.get("search") or "").strip()
    path = f"{resource}/search" if search else resource
    params: dict[str, Any] = {"page": page}
    if search:
        params["query"] = search
    body = await call(ctx, "GET", 7, path, params=params)
    raw = [r for r in (body or {}).get(resource) or [] if isinstance(r, dict)]
    return [r for r in raw if not r.get("deleted")], str(page + 1) if raw else None
