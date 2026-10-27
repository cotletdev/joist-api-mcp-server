#!/usr/bin/env python3
"""Revenue or sales tax for one month from Joist's Reports page, with the total and every row.

python monthly_report.py --month 2026-10
python monthly_report.py --month 2026-10 --report sales_tax --out tax-2026-10.csv
"""

import argparse
import calendar
import sys

from joist_api_mcp.scripting import call, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n", 1)[0])
    parser.add_argument("--month", required=True, help="YYYY-MM")
    parser.add_argument("--report", choices=["revenue", "invoices", "estimates", "sales_tax"], default="revenue")
    parser.add_argument("--out", help="Save the rows to .csv or .json instead of printing")
    args = parser.parse_args()

    year, month = (int(part) for part in args.month.split("-"))
    params = {
        "report": args.report,
        "from": f"{args.month}-01",
        "to": f"{args.month}-{calendar.monthrange(year, month)[1]:02d}",
    }
    rows = []
    while True:
        page = call("get_report", {**params, "limit": 50})
        rows += page["rows"]
        if not page.get("next_cursor"):
            break
        params["cursor"] = page["next_cursor"]
    print(f"{args.report} {page['from']} to {page['to']}: total {page['total']}, {len(rows)} rows", file=sys.stderr)
    write_rows(rows, args.out)


if __name__ == "__main__":
    run(main)
