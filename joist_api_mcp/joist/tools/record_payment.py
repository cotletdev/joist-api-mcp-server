"""Record payment: a manual payment on an invoice (`POST /v7/{user}/invoices/{id}/transactions/payments`), as the
panel's Record Payment saves it. Joist then moves the invoice to partial or paid."""

from __future__ import annotations

from datetime import UTC, datetime, time
from typing import TYPE_CHECKING, Any

from joist_api_mcp.core.errors import ErrorCode, ToolError
from joist_api_mcp.core.tools import tool
from joist_api_mcp.joist.tools._api import ID_SCHEMA, call, parse_day, today
from joist_api_mcp.joist.tools._documents import read

if TYPE_CHECKING:
    from joist_api_mcp.core.context import ToolContext

METHODS = ("cash", "check", "credit_card", "bank_transfer")

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "invoice_id": {**ID_SCHEMA, "description": "From list_invoices."},
        "amount": {"type": "number", "exclusiveMinimum": 0, "description": "Amount received, e.g. 1200.50."},
        "method": {"type": "string", "enum": list(METHODS), "description": "How the client paid."},
        "paid_on": {"type": "string", "format": "date", "description": "Payment date. Default: today."},
    },
    "required": ["invoice_id", "amount", "method"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "payment_id": "0ff33ac4-01f9-4955-9fa8-aba4a78602aa",
    "invoice_id": "71977284",
    "number": "1",
    "total": 521.24,
    "amount_paid": 521.24,
    "balance_due": 0.0,
    "status": "paid",
    "payments": [
        {
            "payment_id": "5b1f0c2e-8f3a-4d7e-9a61-2c4b8e7d1f90",
            "type": "payment",
            "amount": 130.31,
            "method": "cash",
            "paid_on": "2026-10-26",
            "status": "succeeded",
            "source": "manual",
        },
        {
            "payment_id": "0ff33ac4-01f9-4955-9fa8-aba4a78602aa",
            "type": "payment",
            "amount": 390.93,
            "method": "check",
            "paid_on": "2026-10-27",
            "status": "succeeded",
            "source": "manual",
        },
    ],
}


def _paid_at(ctx: ToolContext, value: Any) -> str:
    """Now for today, noon in the user's zone for another day (so the date never shifts), in UTC."""
    day = parse_day(value, "paid_on") if value else today(ctx)
    if day > today(ctx):
        raise ToolError("paid_on cannot be in the future.", ErrorCode.INVALID_INPUT)
    moment = datetime.now(ctx.user_zone) if day == today(ctx) else datetime.combine(day, time(12), tzinfo=ctx.user_zone)
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")


@tool(
    name="record_payment",
    title="Record payment",
    access="write",
    description="Record a cash, check, credit card or bank transfer payment on an invoice; paid in full moves to Paid.",
    details=(
        "Records a payment received outside Joist Payments, as Record Payment does in Joist. Partial payments "
        "are allowed and an invoice can hold several; an amount above the balance due or a date in the future is "
        "refused. Once paid in "
        "full the invoice moves from Active to Paid. Check get_invoice first so the same check is not entered "
        "twice. By default you confirm each call, and you can switch that off for this tool."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /invoices/{invoice_id}/payments",
    example_response=EXAMPLE_RESPONSE,
)
async def record_payment(ctx: ToolContext, args: dict[str, Any]) -> Any:
    invoice_id = str(args["invoice_id"])
    invoice = await read(ctx, "invoice", invoice_id)
    amount = round(float(args["amount"]), 2)
    if amount > invoice["balance_due"] + 0.001:
        raise ToolError(
            f"The balance due is {invoice['balance_due']:.2f}; the amount is more.", ErrorCode.INVALID_INPUT
        )
    payment = {
        "amount_cents": f"{round(amount * 100)}.00",
        "deleted": False,
        "method": args["method"],
        "invoice_id": invoice_id,
        "paid_at": _paid_at(ctx, args.get("paid_on")),
        "source": "manual",
    }
    body = await call(ctx, "POST", 7, f"invoices/{invoice_id}/transactions/payments", body={"payment": payment})
    saved = (body or {}).get("payment") or {}
    if not saved.get("id"):
        raise ToolError("Joist did not record the payment.", ErrorCode.TARGET_ERROR)
    after = await read(ctx, "invoice", invoice_id)
    return {
        "payment_id": str(saved["id"]),
        "invoice_id": invoice_id,
        "number": after["number"],
        "total": after["total"],
        "amount_paid": after["amount_paid"],
        "balance_due": after["balance_due"],
        "status": after["status"],
        "payments": after["payments"],
    }
