"""Create estimate: a saved, unsent estimate for a client (`POST /v6/{user}/estimates`, number from `next_doc_id`)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from joist_api_mcp.core.tools import tool
from joist_api_mcp.joist.tools._api import ID_SCHEMA
from joist_api_mcp.joist.tools._documents import LINE_ITEMS_SCHEMA, TERMS_PROPERTIES, create, expiry
from joist_api_mcp.joist.tools._examples import ESTIMATE

if TYPE_CHECKING:
    from joist_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "client_id": {**ID_SCHEMA, "description": "From list_clients or add_client."},
        "line_items": {
            **LINE_ITEMS_SCHEMA,
            "description": "Lines: name, rate, optional quantity, description, item_id.",
        },
        **TERMS_PROPERTIES,
        "expires_on": {"type": "string", "format": "date", "description": "Last day the estimate is valid."},
        "document_date": {"type": "string", "format": "date", "description": "Estimate date. Default: today."},
    },
    "required": ["client_id", "line_items"],
    "additionalProperties": False,
}


@tool(
    name="create_estimate",
    title="Create estimate",
    access="write",
    description="New saved estimate with line items, tax, discount, deposit and expiry. Nothing is sent to the client.",
    details=(
        "Creates an estimate for a client with the next estimate number, copying the client's name, email, phone "
        "and address as Joist does. tax_rate applies one percent to every line, reusing your saved rate with that "
        "percent or adding one; tax_id picks a saved rate. A deposit shows as Deposit Due. expires_on cannot be "
        "in the past. Nothing is sent: the client sees it only after send_estimate. Joist computes the total."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /clients/{client_id}/estimates",
    example_response={**ESTIMATE, "status": "draft", "email_status": "unsent"},
)
async def create_estimate(ctx: ToolContext, args: dict[str, Any]) -> Any:
    extra: dict[str, Any] = {"generate_invoice_on_approval": False}
    if args.get("expires_on"):
        extra["expires_at"] = expiry(ctx, args["expires_on"])
    return await create(ctx, "estimate", args, extra)
