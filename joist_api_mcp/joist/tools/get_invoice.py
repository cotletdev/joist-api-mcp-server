"""Get invoice: one invoice with lines, taxes and deposit (`/v6/{user}/invoices/{id}/`) and its payments and refunds
(`/v7/{user}/invoices/{id}/transactions`)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from joist_api_mcp.core.tools import tool
from joist_api_mcp.joist.tools._api import ID_SCHEMA
from joist_api_mcp.joist.tools._documents import read
from joist_api_mcp.joist.tools._examples import INVOICE

if TYPE_CHECKING:
    from joist_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"invoice_id": {**ID_SCHEMA, "description": "From list_invoices."}},
    "required": ["invoice_id"],
    "additionalProperties": False,
}


@tool(
    name="get_invoice",
    title="Get invoice",
    access="read",
    description="Full invoice: client, line items, tax, discount, deposit, due date, balance and every payment.",
    details=(
        "Returns one invoice with its client, every line item with its taxes, subtotal, discount, tax, total, "
        "requested deposit, payment terms and due date, amount paid, balance due, overdue, the estimate it came "
        "from, and the payments and refunds recorded on it. Check the payments before recording another."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /invoices/{invoice_id}",
    example_response=INVOICE,
)
async def get_invoice(ctx: ToolContext, args: dict[str, Any]) -> Any:
    return await read(ctx, "invoice", str(args["invoice_id"]))
