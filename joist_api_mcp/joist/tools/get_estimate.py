"""Get estimate: one estimate with lines, taxes, discount and deposit (`/v6/{user}/estimates/{id}/`)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from joist_api_mcp.core.tools import tool
from joist_api_mcp.joist.tools._api import ID_SCHEMA
from joist_api_mcp.joist.tools._documents import read
from joist_api_mcp.joist.tools._examples import ESTIMATE

if TYPE_CHECKING:
    from joist_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"estimate_id": {**ID_SCHEMA, "description": "From list_estimates."}},
    "required": ["estimate_id"],
    "additionalProperties": False,
}


@tool(
    name="get_estimate",
    title="Get estimate",
    access="read",
    description="Full estimate: client, line items, tax, discount, deposit, expiry, approval and signature.",
    details=(
        "Returns one estimate with its client, every line item with its taxes, subtotal, discount, tax, total, "
        "requested deposit, expiry, approval status, signature date and the client's link. Read it before "
        "changing or sending the estimate."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /estimates/{estimate_id}",
    example_response=ESTIMATE,
)
async def get_estimate(ctx: ToolContext, args: dict[str, Any]) -> Any:
    return await read(ctx, "estimate", str(args["estimate_id"]))
