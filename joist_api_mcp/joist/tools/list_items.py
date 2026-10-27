"""List items: saved items (`/v7/{user}/items[/search]`) and, on the first page, the tax rates (`/v6/{user}/taxes`)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from joist_api_mcp.core.tools import tool
from joist_api_mcp.joist.tools._api import call, number
from joist_api_mcp.joist.tools._clients import item_row, paged

if TYPE_CHECKING:
    from joist_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "search": {"type": "string", "maxLength": 100, "description": "Part of the item name."},
        "cursor": {"type": "string", "description": "next_cursor from the previous call."},
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "items": [
        {
            "item_id": "105580562",
            "name": "Drywall repair (per sq ft)",
            "description": "Patch, tape, mud and sand",
            "rate": 4.5,
            "quantity": 1.0,
            "tax_ids": [],
        }
    ],
    "taxes": [{"tax_id": "1371277", "name": "NC Sales Tax", "rate": 7.25}],
    "next_cursor": "2",
}


@tool(
    name="list_items",
    title="List items",
    access="read",
    description="Saved items from your Items list with rate and description, plus your tax rates.",
    details=(
        "Lists the items you saved in Joist, one Joist page per call, or the matches of search on the name. "
        "Reuse their names and rates as line items (item_id) instead of guessing prices. The first page also "
        "lists your tax rates (tax_id for create_estimate and create_invoice); later pages leave taxes empty. "
        "Pass next_cursor back as cursor; an empty page ends the list."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /items",
    example_response=EXAMPLE_RESPONSE,
)
async def list_items(ctx: ToolContext, args: dict[str, Any]) -> Any:
    rows, cursor = await paged(ctx, "items", args)
    taxes: list[dict[str, Any]] = []
    if not args.get("cursor"):
        body = await call(ctx, "GET", 6, "taxes", params={"fetch_all": "true"})
        taxes = [
            {"tax_id": str(t.get("id")), "name": t.get("name"), "rate": number(t.get("amount"))}
            for t in (body or {}).get("taxes") or []
            if not t.get("deleted")
        ]
    return {"items": [item_row(r) for r in rows], "taxes": taxes, "next_cursor": cursor}
