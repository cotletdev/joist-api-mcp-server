"""Delete estimate: `DELETE /v6/{user}/estimates/{id}` (the panel's More > Delete)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from joist_api_mcp.core.tools import tool
from joist_api_mcp.joist.tools._api import ID_SCHEMA, call
from joist_api_mcp.joist.tools._documents import fetch

if TYPE_CHECKING:
    from joist_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"estimate_id": {**ID_SCHEMA, "description": "From list_estimates."}},
    "required": ["estimate_id"],
    "additionalProperties": False,
}


@tool(
    name="delete_estimate",
    title="Delete estimate",
    access="write",
    description="Delete an estimate for good.",
    details=(
        "Deletes the estimate from Joist; it cannot be undone and the client's link stops working. An invoice "
        "made from it stays."
    ),
    input_schema=INPUT_SCHEMA,
    route="DELETE /estimates/{estimate_id}",
    example_response={"estimate_id": "52711230", "number": "2", "deleted": True},
)
async def delete_estimate(ctx: ToolContext, args: dict[str, Any]) -> Any:
    estimate_id = str(args["estimate_id"])
    current = await fetch(ctx, "estimate", estimate_id)
    await call(ctx, "DELETE", 6, f"estimates/{estimate_id}", what="Estimate")
    return {"estimate_id": estimate_id, "number": current.get("doc_id"), "deleted": True}
