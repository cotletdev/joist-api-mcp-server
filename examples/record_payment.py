#!/usr/bin/env python3
"""Record a check, cash, card or bank transfer payment on a Joist invoice, found by its number.

    python record_payment.py --invoice 1042 --amount 390.93 --method check
    python record_payment.py --invoice 1042 --amount 200 --method cash --date 2026-10-20

Paid in full moves the invoice to Paid. No money moves: this only records what the client already paid you.
"""

import argparse
import json
import sys

from joist_api_mcp.scripting import call, paginate, run


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n", 1)[0])
    parser.add_argument("--invoice", required=True, help="Invoice number, as shown in Joist")
    parser.add_argument("--amount", type=float, required=True)
    parser.add_argument("--method", choices=["cash", "check", "credit_card", "bank_transfer"], required=True)
    parser.add_argument("--date", help="Payment date, YYYY-MM-DD. Default: today")
    args = parser.parse_args()

    found = [
        i
        for i in paginate("list_invoices", {"view": "active", "search": args.invoice, "limit": 50}, "invoices")
        if i["number"] == args.invoice
    ]
    if not found:
        sys.exit(f"No unpaid invoice #{args.invoice}.")
    invoice = found[0]
    if args.amount > invoice["balance_due"]:
        sys.exit(f"Invoice #{args.invoice} has {invoice['balance_due']} due, less than {args.amount}.")
    params = {"invoice_id": invoice["invoice_id"], "amount": args.amount, "method": args.method, "paid_on": args.date}
    print(json.dumps(call("record_payment", params), indent=2))


if __name__ == "__main__":
    run(main)
