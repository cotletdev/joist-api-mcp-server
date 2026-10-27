"""List clients: the Clients list, or Joist's client search (`/v7/{user}/contacts[/search]`)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from joist_api_mcp.core.tools import tool
from joist_api_mcp.joist.tools._clients import client_row, paged

if TYPE_CHECKING:
    from joist_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "search": {"type": "string", "maxLength": 100, "description": "Part of a name, email, phone or address."},
        "cursor": {"type": "string", "description": "next_cursor from the previous call."},
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "clients": [
        {
            "client_id": "56285802",
            "name": "Maple Street Dental",
            "email": "office@example.com",
            "phone": "9195550142",
            "address": "410 Fayetteville St, Raleigh, NC 27601",
            "notes": "Front office remodel",
            "tags": [],
            "last_payment_on": "2026-10-26",
        }
    ],
    "next_cursor": "2",
}


@tool(
    name="list_clients",
    title="List clients",
    access="read",
    description="Clients in your account with name, email, phone and address.",
    details=(
        "Lists your Joist clients A to Z, one Joist page per call, or the matches of search (name, email, phone "
        "or address). Pass next_cursor back as cursor; an empty page ends the list. client_id goes to "
        "create_estimate, create_invoice and the client filter of list_estimates and list_invoices."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /clients",
    example_response=EXAMPLE_RESPONSE,
)
async def list_clients(ctx: ToolContext, args: dict[str, Any]) -> Any:
    rows, cursor = await paged(ctx, "contacts", args)
    return {"clients": [client_row(ctx, r) for r in rows], "next_cursor": cursor}
