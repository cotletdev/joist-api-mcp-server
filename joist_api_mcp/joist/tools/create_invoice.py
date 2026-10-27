"""Create invoice: a saved, unsent invoice without an estimate (`POST /v6/{user}/invoices`)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from joist_api_mcp.core.tools import tool
from joist_api_mcp.joist.tools._api import ID_SCHEMA
from joist_api_mcp.joist.tools._documents import LINE_ITEMS_SCHEMA, TERMS_PROPERTIES, create
from joist_api_mcp.joist.tools._examples import INVOICE

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
        "payment_terms_days": {
            "type": "integer",
            "minimum": 0,
            "maximum": 365,
            "default": 0,
            "description": "Days after the invoice date the payment is due (0: due on receipt).",
        },
        "document_date": {"type": "string", "format": "date", "description": "Invoice date. Default: today."},
    },
    "required": ["client_id", "line_items"],
    "additionalProperties": False,
}


@tool(
    name="create_invoice",
    title="Create invoice",
    access="write",
    description="New saved invoice for a client without an estimate. Nothing is sent to the client.",
    details=(
        "Creates an invoice with the next invoice number, the client's details, line items, tax, discount, "
        "deposit and payment terms (due date = invoice date + payment_terms_days). For work you estimated, use "
        "convert_estimate_to_invoice instead. Nothing is sent: the client sees it only after send_invoice."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /clients/{client_id}/invoices",
    example_response={
        **INVOICE,
        "status": "draft",
        "email_status": "unsent",
        "amount_paid": 0.0,
        "balance_due": 521.24,
        "from_estimate_id": None,
        "payments": [],
    },
)
async def create_invoice(ctx: ToolContext, args: dict[str, Any]) -> Any:
    return await create(ctx, "invoice", args, {"days_to_pay": int(args.get("payment_terms_days") or 0)})
