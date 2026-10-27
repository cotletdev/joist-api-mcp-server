"""Update estimate: change fields of an estimate with a partial `PUT /v6/{user}/estimates/{id}` (nested attributes:
old lines and taxes removed with `_destroy`, new ones added)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from joist_api_mcp.core.errors import ErrorCode, ToolError
from joist_api_mcp.core.tools import tool
from joist_api_mcp.joist.tools._api import ID_SCHEMA, call
from joist_api_mcp.joist.tools._documents import (
    LINE_ITEMS_SCHEMA,
    TERMS_PROPERTIES,
    expiry,
    fetch,
    lines,
    money_terms,
    new_lines,
    resolve_tax,
    shape,
    tax_rows,
)
from joist_api_mcp.joist.tools._examples import ESTIMATE

if TYPE_CHECKING:
    from joist_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "estimate_id": {**ID_SCHEMA, "description": "From list_estimates."},
        "line_items": {**LINE_ITEMS_SCHEMA, "description": "Replaces every line. Leave out to keep the lines."},
        **TERMS_PROPERTIES,
        "discount": {**TERMS_PROPERTIES["discount"], "type": ["object", "null"], "description": "null removes it."},
        "deposit": {**TERMS_PROPERTIES["deposit"], "type": ["object", "null"], "description": "null removes it."},
        "remove_tax": {"type": "boolean", "description": "true takes the tax off every line."},
        "expires_on": {"type": "string", "format": "date", "description": "New last valid day."},
    },
    "required": ["estimate_id"],
    "additionalProperties": False,
}


def _old_tax(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    for row in rows:
        for tax in row.get("estimate_item_taxes") or []:
            if not tax.get("deleted"):
                return {"id": tax.get("tax_id"), "name": tax.get("name"), "amount": tax.get("amount")}
    return None


def _retaxed(rows: list[dict[str, Any]], tax: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Every kept line with its old tax rows removed and the new one (if any) added."""
    found = []
    for row in rows:
        old = [
            {"id": t.get("id"), "_destroy": True} for t in row.get("estimate_item_taxes") or [] if not t.get("deleted")
        ]
        new = tax_rows("estimate", tax)["estimate_item_taxes_attributes"] if tax else []
        found.append({"id": row.get("id"), "estimate_item_taxes_attributes": old + new})
    return found


@tool(
    name="update_estimate",
    title="Update estimate",
    access="write",
    description="Change an estimate's lines, tax, discount, deposit, expiry, notes or PO number. Nothing is sent.",
    details=(
        "Changes only the fields you pass. line_items replaces every line (the tax stays unless you pass "
        "tax_rate, tax_id or remove_tax). tax_rate or tax_id alone re-taxes the current lines. discount or "
        "deposit null removes it. Joist recomputes the total. Nothing is sent; a client who already got the "
        "estimate sees the change behind the same link."
    ),
    input_schema=INPUT_SCHEMA,
    route="PATCH /estimates/{estimate_id}",
    example_response=ESTIMATE,
)
async def update_estimate(ctx: ToolContext, args: dict[str, Any]) -> Any:
    estimate_id = str(args["estimate_id"])
    if len(args) == 1:
        raise ToolError("Pass at least one field to change.", ErrorCode.INVALID_INPUT)
    current = await fetch(ctx, "estimate", estimate_id)
    rows = lines(current, "estimate")
    taxing = args.get("tax_id") is not None or args.get("tax_rate") is not None or bool(args.get("remove_tax"))
    tax = None if args.get("remove_tax") else await resolve_tax(ctx, args) if taxing else _old_tax(rows)
    fields = money_terms(args, current)
    if "discount" in args and args["discount"] is None:
        fields.update({"discount_percent": None, "discount_amount": None})
    if args.get("line_items"):
        removed: list[dict[str, Any]] = [{"id": r.get("id"), "_destroy": True} for r in rows]
        fields["estimate_items_attributes"] = removed + new_lines("estimate", args["line_items"], tax, len(rows))
    elif taxing:
        fields["estimate_items_attributes"] = _retaxed(rows, tax)
    if args.get("expires_on"):
        fields["expires_at"] = expiry(ctx, args["expires_on"])
    body = await call(ctx, "PUT", 6, f"estimates/{estimate_id}", body={"estimate": fields}, what="Estimate")
    updated = (body or {}).get("estimate") or await fetch(ctx, "estimate", estimate_id)
    return shape(ctx, updated, "estimate")
