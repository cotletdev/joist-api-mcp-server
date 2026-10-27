"""Delete invoice: `DELETE /v6/{user}/invoices/{id}` (the panel's More > Delete), refused with payments on it."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from joist_api_mcp.core.errors import ErrorCode, ToolError
from joist_api_mcp.core.tools import tool
from joist_api_mcp.joist.tools._api import ID_SCHEMA, call
from joist_api_mcp.joist.tools._documents import fetch, payments

if TYPE_CHECKING:
    from joist_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"invoice_id": {**ID_SCHEMA, "description": "From list_invoices."}},
    "required": ["invoice_id"],
    "additionalProperties": False,
}


@tool(
    name="delete_invoice",
    title="Delete invoice",
    access="write",
    description="Delete an invoice that has no payments, for good.",
    details=(
        "Deletes the invoice from Joist; it cannot be undone and the client's link stops working. An invoice "
        "with payments recorded is refused, so your payment history stays."
    ),
    input_schema=INPUT_SCHEMA,
    route="DELETE /invoices/{invoice_id}",
    example_response={"invoice_id": "71980012", "number": "2", "deleted": True},
)
async def delete_invoice(ctx: ToolContext, args: dict[str, Any]) -> Any:
    invoice_id = str(args["invoice_id"])
    current = await fetch(ctx, "invoice", invoice_id)
    if any(p["type"] == "payment" for p in await payments(ctx, invoice_id)):
        raise ToolError("This invoice has payments recorded; it is not deleted.", ErrorCode.INVALID_INPUT)
    await call(ctx, "DELETE", 6, f"invoices/{invoice_id}", what="Invoice")
    return {"invoice_id": invoice_id, "number": current.get("doc_id"), "deleted": True}
