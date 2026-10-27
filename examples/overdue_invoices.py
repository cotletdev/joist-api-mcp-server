#!/usr/bin/env python3
"""Overdue Joist invoices: client, total, amount paid, balance due and due date, oldest first.

python overdue_invoices.py
python overdue_invoices.py --out overdue.csv
"""

import argparse

from joist_api_mcp.scripting import paginate, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n", 1)[0])
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    rows = list(paginate("list_invoices", {"view": "overdue", "limit": 50}, "invoices"))
    rows.sort(key=lambda i: i.get("due_date") or "")
    write_rows(rows, args.out)


if __name__ == "__main__":
    run(main)
