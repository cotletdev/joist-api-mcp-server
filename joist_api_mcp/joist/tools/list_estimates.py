"""List estimates: the Estimates tabs (`/v8/{user}/estimates`, cursor paging)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from joist_api_mcp.core.helpers import limit
from joist_api_mcp.core.tools import tool
from joist_api_mcp.joist.tools._api import ID_SCHEMA
from joist_api_mcp.joist.tools._documents import document_list, list_row

if TYPE_CHECKING:
    from joist_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "approval": {
            "type": "string",
            "enum": ["all", "pending", "approved", "declined"],
            "default": "all",
            "description": "The panel's tabs: pending, approved, declined, or all (default).",
        },
        "search": {"type": "string", "maxLength": 100, "description": "Client name or estimate number."},
        "client_id": {**ID_SCHEMA, "description": "Only this client's estimates (list_clients)."},
        "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 40},
        "cursor": {"type": "string", "description": "next_cursor from the previous call."},
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "estimates": [
        {
            "estimate_id": "52709714",
            "number": "1",
            "client": "Maple Street Dental",
            "document_date": "2026-10-26",
            "total": 521.24,
            "currency": "USD",
            "status": "invoiced",
            "email_status": "sent",
            "signed": False,
            "po_number": "PO-2231",
            "approval_status": "approved",
            "expires_on": "2026-11-26",
        }
    ],
    "next_cursor": None,
}


@tool(
    name="list_estimates",
    title="List estimates",
    access="read",
    description="Estimates with number, client, total, expiry, status, approval, and whether it was emailed or signed.",
    details=(
        "Lists estimates newest first, from one of the panel's tabs (approval pending, approved, declined or all), "
        "optionally searched by client name or number or limited to one client. status is Joist's: draft, issued "
        "(sent), invoiced (an invoice was made from it). email_status says whether it was emailed (unsent, sent) "
        "and signed whether the client signed it. Pass next_cursor back as cursor."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /estimates",
    example_response=EXAMPLE_RESPONSE,
)
async def list_estimates(ctx: ToolContext, args: dict[str, Any]) -> Any:
    approval = str(args.get("approval") or "all")
    rows, cursor = await document_list(
        ctx, "estimate", args, "" if approval == "all" else approval, limit(args, 40, 100)
    )
    return {"estimates": [list_row(ctx, r, "estimate") for r in rows], "next_cursor": cursor}
