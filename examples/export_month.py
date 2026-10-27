#!/usr/bin/env python3
"""Joist's monthly CSV of invoices or estimates, the same file the panel exports, for your accountant.

python export_month.py --month 2026-10 --out invoices-2026-10.csv
python export_month.py --type estimates --month 2026-10
"""

import argparse
import sys
from pathlib import Path

from joist_api_mcp.scripting import call, run


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n", 1)[0])
    parser.add_argument("--type", choices=["invoices", "estimates"], default="invoices")
    parser.add_argument("--month", required=True, help="YYYY-MM")
    parser.add_argument("--out", help="Save the CSV here instead of printing it")
    args = parser.parse_args()

    export = call("export_documents", {"type": args.type, "month": args.month})
    if not args.out:
        print(export["csv"], end="")
        return
    Path(args.out).write_text(export["csv"], encoding="utf-8")
    print(f"Saved {len(export['rows'])} {args.type} to {args.out}", file=sys.stderr)


if __name__ == "__main__":
    run(main)
