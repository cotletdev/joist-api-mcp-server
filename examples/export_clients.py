#!/usr/bin/env python3
"""Export your Joist clients to CSV or JSON: name, email, phone, address, notes, last payment.

    python export_clients.py --out clients.csv
    python export_clients.py --search dental

Pages are followed automatically.
"""

import argparse

from joist_api_mcp.scripting import paginate, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n", 1)[0])
    parser.add_argument("--search", help="Part of a name, email, phone or address")
    parser.add_argument("--max", type=int, help="Stop after this many clients")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    rows = list(paginate("list_clients", {"search": args.search}, "clients", args.max))
    write_rows(rows, args.out)


if __name__ == "__main__":
    run(main)
