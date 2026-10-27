"""Send invoice: email it to the client from Joist (`_send.py`)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from joist_api_mcp.core.tools import tool
from joist_api_mcp.joist.tools._send import input_schema, send

if TYPE_CHECKING:
    from joist_api_mcp.core.context import ToolContext


@tool(
    name="send_invoice",
    title="Send invoice",
    access="write",
    confirm=True,
    description="Email the invoice to the client from Joist with its link and PDF.",
    details=(
        "Emails the invoice from Joist, as its Send button does: the client gets a link to view and pay it "
        "and the PDF. Without to it goes to the client email on the document; subject and message default to "
        "Joist's subject and your saved invoice message. A draft becomes issued; a sent "
        "invoice can be sent again. By default you confirm each call, and you can switch that off for this tool."
    ),
    input_schema=input_schema("invoice"),
    route="POST /invoices/{invoice_id}/send",
    example_response={
        "invoice_id": "71978164",
        "number": "3",
        "emailed_to": ["office@example.com"],
        "subject": "Your Invoice #3 from Riverside Remodeling LLC",
        "status": "issued",
        "email_status": "sent",
        "public_url": "https://client.joistapp.com/invoices/7c9f786922bf3f0a3493939e",
    },
)
async def send_invoice(ctx: ToolContext, args: dict[str, Any]) -> Any:
    return await send(ctx, "invoice", args)
