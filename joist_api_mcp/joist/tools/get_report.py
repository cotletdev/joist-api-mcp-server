"""Get report: one of the Reports page's four reports (`POST /{user}/core_insights`, GraphQL, no API version).

Joist fills the reports once a day ("Report Numbers Are Updated Daily"), so a new document or payment appears the
next day; until then the rows are empty and the totals 0.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from joist_api_mcp.core.errors import ErrorCode, ToolError
from joist_api_mcp.core.helpers import limit, page_cursor
from joist_api_mcp.core.tools import tool
from joist_api_mcp.joist.tools import _report_queries as queries
from joist_api_mcp.joist.tools._api import call, money, parse_day

if TYPE_CHECKING:
    from joist_api_mcp.core.context import ToolContext

# report: (operation, GraphQL field, query text)
REPORTS = {
    "revenue": ("GetRevenuePaged", "revenue", queries.REVENUE),
    "invoices": ("GetInvoicesPaged", "invoices", queries.INVOICES),
    "estimates": ("GetEstimatesPaged", "estimates", queries.ESTIMATES),
    "sales_tax": ("GetSalesTaxPaged", "salesTaxes", queries.SALES_TAX),
}
TOTAL_OF = {"revenue": "revenueTotal", "invoices": "invoiceTotal", "estimates": "estimatesTotal"}
MONEY = {
    "invoice_total",
    "payment_amount",
    "balance_at_beginning_of_period",
    "balance_at_end_of_period",
    "discount",
    "markup",
    "total",
    "amount_outstanding",
    "subtotal",
    "tax_collected",
}
MAX_DAYS = 366

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "report": {
            "type": "string",
            "enum": list(REPORTS),
            "description": (
                "revenue (payments received per invoice, with balances at the start and end of the period), "
                "invoices (status, total, balance and due date), estimates (status, total, expiry) or sales_tax "
                "(tax collected per tax name and invoice)."
            ),
        },
        "from": {"type": "string", "format": "date", "description": "First day of the period."},
        "to": {"type": "string", "format": "date", "description": "Last day, up to a year after from."},
        "client": {"type": "string", "maxLength": 255, "description": "Only this client, by exact name."},
        "tax_name": {"type": "string", "maxLength": 255, "description": "sales_tax: only this tax, by name."},
        "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 50},
        "cursor": {"type": "string", "description": "next_cursor from the previous call."},
    },
    "required": ["report", "from", "to"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "report": "invoices",
    "from": "2026-10-01",
    "to": "2026-10-31",
    "total": 521.24,
    "total_entries": 1,
    "rows": [
        {
            "id": "71977284",
            "doc_id": "1",
            "name": "Maple Street Dental",
            "document_date": "2026-10-26",
            "due_date": "2026-10-26",
            "fully_paid_date": None,
            "status": "partial",
            "total": 521.24,
            "discount": 54.0,
            "taxes": "35.24",
            "markup": 0.0,
            "amount_outstanding": 390.93,
            "currency_code": "USD",
        }
    ],
    "next_cursor": None,
}


def _row(raw: dict[str, Any]) -> dict[str, Any]:
    found: dict[str, Any] = {}
    for key, value in raw.items():
        if key in ("__typename", "original_id"):
            continue
        if key in MONEY and value not in (None, ""):
            found[key] = money(value)
        elif key == "id" and value is not None:
            found[key] = str(value)
        else:
            found[key] = value
    return found


@tool(
    name="get_report",
    title="Get report",
    access="read",
    description="A Joist report for a date range: revenue, invoices, estimates or sales tax, with the period total.",
    details=(
        "Returns one of the reports on Joist's Reports page for a date range, optionally for one client: revenue "
        "received per invoice (partial payments included), invoice statuses and balances, estimate statuses, or "
        "sales tax collected per tax. total is the report's total for the period. Joist updates report numbers "
        "once a day, so today's documents and payments show tomorrow. Reports are part of Joist Elite (and the "
        "trial). Pass next_cursor back as cursor."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /reports/{report}",
    example_response=EXAMPLE_RESPONSE,
)
async def get_report(ctx: ToolContext, args: dict[str, Any]) -> Any:
    report = str(args["report"])
    start, end = parse_day(args["from"], "from"), parse_day(args["to"], "to")
    if end < start or (end - start).days > MAX_DAYS:
        raise ToolError("to must be on or after from, at most a year later.", ErrorCode.INVALID_INPUT)
    operation, field, query = REPORTS[report]
    # Joist answers an empty page above 50 entries per page (checked 27.10.2026).
    page, size = page_cursor(args.get("cursor")), limit(args, 50, 50)
    variables: dict[str, Any] = {
        "minDateRange": start.isoformat(),
        "maxDateRange": end.isoformat(),
        "pageNum": page - 1,
        "numEntriesPerPage": size,
        "sortDirection": "desc",
    }
    if args.get("client"):
        variables["clientNames"] = [args["client"]]
    if report == "sales_tax" and args.get("tax_name"):
        variables["taxNames"] = [args["tax_name"]]
    body = await call(
        ctx, "POST", None, "core_insights", body={"operationName": operation, "variables": variables, "query": query}
    )
    if (body or {}).get("errors") and not (body or {}).get("data"):
        raise ToolError("Joist could not build this report.", ErrorCode.TARGET_ERROR)
    found = (((body or {}).get("data") or {}).get(field)) or {}
    rows = [_row(r) for r in found.get("reports") or [] if isinstance(r, dict)]
    entries = int(found.get("total_entries") or 0)
    total = money(found.get("grand_total_amount"))
    if report in TOTAL_OF and not args.get("client"):
        grand = await call(
            ctx,
            "POST",
            None,
            "core_insights",
            body={
                "operationName": "GetReportsGrandTotals",
                "variables": {"minDateRange": start.isoformat(), "maxDateRange": end.isoformat()},
                "query": queries.GRAND_TOTALS,
            },
        )
        value = ((((grand or {}).get("data") or {}).get("reportsGrandTotals")) or {}).get(TOTAL_OF[report])
        if value is not None:
            total = money(value)
    return {
        "report": report,
        "from": start.isoformat(),
        "to": end.isoformat(),
        "total": total,
        "total_entries": entries,
        "rows": rows,
        "next_cursor": str(page + 1) if page * size < entries else None,
    }
