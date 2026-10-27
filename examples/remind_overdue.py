#!/usr/bin/env python3
"""Email a reminder for each overdue Joist invoice, with the invoice link and PDF, from your Joist account.

    python remind_overdue.py                       # lists who would get one
    python remind_overdue.py --send --days 7
    python remind_overdue.py --send --message "A friendly reminder: invoice attached."

Without --send nothing is emailed. --days skips invoices less than that many days past due.
"""

import argparse
import json
from datetime import date

from joist_api_mcp.scripting import call, paginate, run


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n", 1)[0])
    parser.add_argument("--days", type=int, default=0, help="Only invoices at least this many days past due")
    parser.add_argument("--message", help="Email text. Default: your invoice email message in Joist")
    parser.add_argument("--send", action="store_true", help="Send the emails")
    args = parser.parse_args()

    today = date.today()
    due = [
        i
        for i in paginate("list_invoices", {"view": "overdue", "limit": 50}, "invoices")
        if i.get("due_date") and (today - date.fromisoformat(i["due_date"])).days >= args.days
    ]
    for invoice in due:
        line = f"#{invoice['number']}  {invoice['client']}  {invoice['balance_due']} due since {invoice['due_date']}"
        if not args.send:
            print(line)
            continue
        params = {"invoice_id": invoice["invoice_id"], "message": args.message}
        print(line, json.dumps(call("send_invoice", params)))
    if not args.send:
        print(f"{len(due)} overdue invoices. Run again with --send to email them.")


if __name__ == "__main__":
    run(main)
