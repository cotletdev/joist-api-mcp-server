"""Send estimate: email it to the client from Joist (`_send.py`)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from joist_api_mcp.core.tools import tool
from joist_api_mcp.joist.tools._send import input_schema, send

if TYPE_CHECKING:
    from joist_api_mcp.core.context import ToolContext


@tool(
    name="send_estimate",
    title="Send estimate",
    access="write",
    confirm=True,
    description="Email the estimate to the client from Joist with its link and PDF.",
    details=(
        "Emails the estimate from Joist, as its Send button does: the client gets a link to view and sign it "
        "and the PDF. Without to it goes to the client email on the document; subject and message default to "
        "Joist's subject and your saved estimate message. A draft becomes issued; a sent "
        "estimate can be sent again. By default you confirm each call, and you can switch that off for this tool."
    ),
    input_schema=input_schema("estimate"),
    route="POST /estimates/{estimate_id}/send",
    example_response={
        "estimate_id": "52710521",
        "number": "3",
        "emailed_to": ["office@example.com"],
        "subject": "Your Estimate #3 from Riverside Remodeling LLC",
        "status": "issued",
        "email_status": "sent",
        "public_url": "https://client.joistapp.com/estimates/7c9f786922bf3f0a3493939e",
    },
)
async def send_estimate(ctx: ToolContext, args: dict[str, Any]) -> Any:
    return await send(ctx, "estimate", args)
