#!/usr/bin/env python3
"""Create a Joist estimate from a job description: finds the client by name (or adds it) and saves the lines.

    python estimate_from_job.py --client "Maple Street Dental" \
        --line "Drywall repair (per sq ft):120:4.50" --line "Paint, two coats:1:380" --tax 7.25 --dry-run
    python estimate_from_job.py --client "Jordan Lee" --email jordan@example.com --line "Deck stain:1:650"

A line is name:quantity:rate. A name that matches a saved item (list_items) keeps that item as its source.
The estimate is saved in Joist and nothing is sent to the client. Send it with send_estimate.
"""

import argparse
import json
import sys
from typing import Any

from joist_api_mcp.scripting import call, paginate, run


def parse_line(text: str, items: dict[str, str]) -> dict[str, Any]:
    name, _, rest = text.rpartition(":")
    name, _, quantity = name.rpartition(":")
    if not name:
        sys.exit(f"Line {text!r} is not name:quantity:rate.")
    line: dict[str, Any] = {"name": name, "quantity": float(quantity), "rate": float(rest)}
    if item_id := items.get(name.lower()):
        line["item_id"] = item_id
    return line


def find_client(name: str) -> dict[str, Any] | None:
    for client in paginate("list_clients", {"search": name}, "clients"):
        if client["name"].lower() == name.lower():
            return client
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n", 1)[0])
    parser.add_argument("--client", required=True, help="Client name, as on the client card")
    parser.add_argument("--email", help="Email for a new client")
    parser.add_argument("--line", action="append", required=True, help="name:quantity:rate, repeat for more lines")
    parser.add_argument("--tax", type=float, help="Tax percent on every line, e.g. 7.25")
    parser.add_argument("--notes", help="Notes shown on the estimate")
    parser.add_argument("--expires", help="Last valid day, YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", help="Show the estimate, save nothing")
    args = parser.parse_args()

    items = {i["name"].lower(): i["item_id"] for i in paginate("list_items", {}, "items")}
    lines = [parse_line(text, items) for text in args.line]
    client = find_client(args.client)
    estimate: dict[str, Any] = {
        "client_id": client["client_id"] if client else "(new client)",
        "line_items": lines,
        "tax_rate": args.tax,
        "notes": args.notes,
        "expires_on": args.expires,
    }
    estimate = {k: v for k, v in estimate.items() if v is not None}
    if args.dry_run:
        print(json.dumps({"client": args.client, "new_client": client is None, "estimate": estimate}, indent=2))
        return
    if client is None:
        client = call("add_client", {"name": args.client, "email": args.email})
    estimate["client_id"] = client["client_id"]
    print(json.dumps(call("create_estimate", estimate), indent=2))


if __name__ == "__main__":
    run(main)
