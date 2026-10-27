"""Add item: a saved item in the Items list (`POST /v7/{user}/items`)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from joist_api_mcp.core.errors import ErrorCode, ToolError
from joist_api_mcp.core.tools import tool
from joist_api_mcp.joist.tools._api import call
from joist_api_mcp.joist.tools._clients import item_row

if TYPE_CHECKING:
    from joist_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1, "maxLength": 255, "description": "Item name."},
        "rate": {"type": "number", "minimum": 0, "description": "Price per unit, e.g. 350."},
        "description": {"type": "string", "maxLength": 5000, "description": "Shown on the line item."},
    },
    "required": ["name", "rate"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "item_id": "105612230",
    "name": "Baseboard, installed (per ft)",
    "description": "Supply, cut and nail",
    "rate": 4.5,
    "quantity": 1.0,
    "tax_ids": [],
}


@tool(
    name="add_item",
    title="Add item",
    access="write",
    description="Save a service or material to your Items list.",
    details=(
        "Saves an item with a name, rate and optional description to your Items list, so later estimates "
        "reuse it. It reaches no one."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /items",
    example_response=EXAMPLE_RESPONSE,
)
async def add_item(ctx: ToolContext, args: dict[str, Any]) -> Any:
    item = {
        "name": args["name"].strip(),
        "price": f"{float(args['rate']):.2f}",
        "notes": args.get("description") or "",
        "quantity": 1,
        "deleted": False,
        "item_taxes_attributes": [],
        "private_notes": [{"type": "text", "content": ""}],
    }
    body = await call(ctx, "POST", 7, "items", body={"item": item})
    created = (body or {}).get("item") or {}
    if not created.get("id"):
        raise ToolError("Joist did not save the item.", ErrorCode.TARGET_ERROR)
    return item_row(created)
