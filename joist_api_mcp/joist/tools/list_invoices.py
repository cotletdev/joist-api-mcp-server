"""List invoices: the Invoices tabs (`/v8/{user}/invoices`), with due date, balance and a computed overdue.

The list gives no due date or balance, so an unpaid row costs one detail read (cached until the invoice changes).
Overdue is not a Joist status: invoice date + payment terms before today with a balance left (`../../MAP.md`, 9).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from joist_api_mcp.core.helpers import limit
from joist_api_mcp.core.tools import tool
from joist_api_mcp.joist.tools._api import ID_SCHEMA
from joist_api_mcp.joist.tools._documents import document_list, invoice_rows

if TYPE_CHECKING:
    from joist_api_mcp.core.context import ToolContext

FILTERS = {"active": "active", "overdue": "active", "paid": "paid", "all": ""}

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "view": {
            "type": "string",
            "enum": list(FILTERS),
            "default": "active",
            "description": "active (not paid in full; default), overdue (active and past due), paid, or all.",
        },
        "search": {"type": "string", "maxLength": 100, "description": "Client name or invoice number."},
        "client_id": {**ID_SCHEMA, "description": "Only this client's invoices (list_clients)."},
        "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 25},
        "cursor": {"type": "string", "description": "next_cursor from the previous call."},
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "invoices": [
        {
            "invoice_id": "71977284",
            "number": "1",
            "client": "Maple Street Dental",
            "document_date": "2026-10-26",
            "total": 521.24,
            "currency": "USD",
            "status": "partial",
            "email_status": "sent",
            "signed": False,
            "po_number": "PO-2231",
            "due_date": "2026-10-26",
            "amount_paid": 130.31,
            "balance_due": 390.93,
            "overdue": False,
        }
    ],
    "next_cursor": None,
}


@tool(
    name="list_invoices",
    title="List invoices",
    access="read",
    description="Invoices with client, total, amount paid, balance due, due date and overdue. Active, paid or all.",
    details=(
        "Lists invoices newest first from the panel's Active tab (not paid in full; default) or Paid tab, or all. "
        "overdue keeps the active ones past their due date, which is the invoice date plus its payment terms. "
        "status is Joist's: draft, issued (sent), partial or paid. Search matches client name or number. Each "
        "page of overdue may hold fewer rows than limit; follow next_cursor until it is null."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /invoices",
    example_response=EXAMPLE_RESPONSE,
)
async def list_invoices(ctx: ToolContext, args: dict[str, Any]) -> Any:
    view = str(args.get("view") or "active")
    rows, cursor = await document_list(ctx, "invoice", args, FILTERS[view], limit(args, 25, 50))
    invoices = await invoice_rows(ctx, rows)
    if view == "overdue":
        invoices = [i for i in invoices if i["overdue"]]
    return {"invoices": invoices, "next_cursor": cursor}
