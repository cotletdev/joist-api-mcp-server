"""Export documents: the monthly CSV of the Estimates or Invoices page
(`GET /v6/{user}/{kind}s/export/{year}/{month}.csv?group_by=issued_at`), parsed into rows."""

from __future__ import annotations

import csv
import io
import re
from typing import TYPE_CHECKING, Any

from joist_api_mcp.core.errors import ErrorCode, ToolError
from joist_api_mcp.core.tools import tool
from joist_api_mcp.joist.tools._api import call

if TYPE_CHECKING:
    from joist_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "type": {"type": "string", "enum": ["estimates", "invoices"]},
        "month": {"type": "string", "pattern": "^[0-9]{4}-(0[1-9]|1[0-2])$", "description": "Month as YYYY-MM."},
    },
    "required": ["type", "month"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "type": "invoices",
    "month": "2026-10",
    "columns": [
        "Invoice #",
        "Client Name",
        "Subtotal",
        "NC Sales Tax",
        "Total",
        "Date Issued",
        "Date Created",
        "Payment Received Less Refunds",
    ],
    "rows": [
        {
            "Invoice #": "1",
            "Client Name": "Maple Street Dental",
            "Subtotal": "486.0",
            "NC Sales Tax": "35.24",
            "Total": "521.24",
            "Date Issued": "2026-10-26",
            "Date Created": "2026-10-26 20:47:12 UTC",
            "Payment Received Less Refunds": "130.31",
        }
    ],
    "csv": (
        "Invoice #,Client Name,Subtotal,NC Sales Tax,Total,Date Issued,Date Created,Payment Received Less Refunds\n"
        "1,Maple Street Dental,486.0,35.24,521.24,2026-10-26,2026-10-26 20:47:12 UTC,130.31\n"
    ),
}

MAX_ROWS = 2000


@tool(
    name="export_documents",
    title="Export documents",
    access="read",
    description="Joist's monthly CSV of estimates or invoices: number, client, subtotal, tax, total, dates, payments.",
    details=(
        "Runs the same export as the Export button on Joist's Estimates or Invoices page for one month, by date "
        "issued: number, client name, subtotal, one column per tax name, total, date issued, date created and, "
        "for invoices, payment received less refunds. Returns the columns, the rows and the CSV text as Joist "
        "made it, at most 2000 rows parsed. Line items are not in the export; use get_estimate or get_invoice."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /documents/export",
    example_response=EXAMPLE_RESPONSE,
)
async def export_documents(ctx: ToolContext, args: dict[str, Any]) -> Any:
    kind = str(args["type"])
    year, month = (int(p) for p in str(args["month"]).split("-"))
    text = await call(ctx, "GET", 6, f"{kind}/export/{year}/{month}.csv", params={"group_by": "issued_at"})
    if not isinstance(text, str):
        raise ToolError("Joist did not return the CSV.", ErrorCode.TARGET_ERROR)
    text = text.lstrip("﻿")
    reader = csv.reader(io.StringIO(text))
    table = [row for row in reader if any(cell.strip() for cell in row)]
    columns = [re.sub(r"\s+", " ", c).strip() for c in table[0]] if table else []
    rows = [dict(zip(columns, row, strict=False)) for row in table[1 : MAX_ROWS + 1]]
    return {"type": kind, "month": args["month"], "columns": columns, "rows": rows, "csv": text}
