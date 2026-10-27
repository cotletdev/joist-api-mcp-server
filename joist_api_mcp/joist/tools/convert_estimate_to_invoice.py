"""Convert estimate to invoice: Generate Invoice (`POST /v6/{user}/estimates/{id}/generate_invoice`)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from joist_api_mcp.core.errors import ErrorCode, ToolError
from joist_api_mcp.core.tools import tool
from joist_api_mcp.joist.tools._api import ID_SCHEMA, call
from joist_api_mcp.joist.tools._documents import fetch, shape
from joist_api_mcp.joist.tools._examples import INVOICE

if TYPE_CHECKING:
    from joist_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"estimate_id": {**ID_SCHEMA, "description": "From list_estimates."}},
    "required": ["estimate_id"],
    "additionalProperties": False,
}


@tool(
    name="convert_estimate_to_invoice",
    title="Convert estimate to invoice",
    access="write",
    description="Generate an invoice with everything from the estimate. Nothing is sent to the client.",
    details=(
        "Does what Generate Invoice does in Joist: a new invoice with the estimate's client, lines, tax, "
        "discount and deposit, and the estimate becomes approved. Joist allows more than one invoice from an "
        "estimate, so an estimate already invoiced is refused here. Nothing is sent until send_invoice."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /estimates/{estimate_id}/convert",
    example_response={**INVOICE, "status": "draft", "email_status": "unsent", "payments": []},
)
async def convert_estimate_to_invoice(ctx: ToolContext, args: dict[str, Any]) -> Any:
    estimate_id = str(args["estimate_id"])
    estimate = await fetch(ctx, "estimate", estimate_id)
    if estimate.get("status") == "invoiced":
        raise ToolError(
            "This estimate already has an invoice (list_invoices with its client finds it).", ErrorCode.INVALID_INPUT
        )
    body = await call(
        ctx, "POST", 6, f"estimates/{estimate_id}/generate_invoice", body={"data": {"is_manual": True}}, what="Estimate"
    )
    invoice = (body or {}).get("invoice") or (body or {}).get("data") or {}
    if not invoice.get("id"):
        raise ToolError("Joist did not make the invoice.", ErrorCode.TARGET_ERROR)
    return shape(ctx, invoice, "invoice", [])
