#!/usr/bin/env python3
"""Turn every approved Joist estimate that has no invoice yet into an invoice, and email it with --send.

    python invoice_approved_estimates.py               # lists what it would do
    python invoice_approved_estimates.py --convert
    python invoice_approved_estimates.py --convert --send

Without --convert nothing changes. --send emails each new invoice to the client email on it.
"""

import argparse
import json

from joist_api_mcp.scripting import call, paginate, run


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n", 1)[0])
    parser.add_argument("--convert", action="store_true", help="Create the invoices")
    parser.add_argument("--send", action="store_true", help="Also email each new invoice")
    args = parser.parse_args()

    todo = [
        e
        for e in paginate("list_estimates", {"approval": "approved", "limit": 100}, "estimates")
        if e.get("status") != "invoiced"
    ]
    if not args.convert:
        for e in todo:
            print(f"Estimate #{e['number']}  {e['client']}  {e['total']} {e['currency']}")
        print(f"{len(todo)} approved estimates without an invoice. Run again with --convert.")
        return
    for e in todo:
        invoice = call("convert_estimate_to_invoice", {"estimate_id": e["estimate_id"]})
        result = {"estimate": e["number"], "client": e["client"], "invoice": invoice}
        if args.send:
            result["sent"] = call("send_invoice", {"invoice_id": invoice["document_id"]})
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run(main)
