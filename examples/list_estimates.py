#!/usr/bin/env python3
"""Your Joist estimates by approval: number, client, total, status, expiry, emailed or signed.

    python list_estimates.py --approval pending
    python list_estimates.py --approval approved --out approved.csv

Pages are followed automatically.
"""

import argparse

from joist_api_mcp.scripting import paginate, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n", 1)[0])
    parser.add_argument("--approval", choices=["all", "pending", "approved", "declined"], default="all")
    parser.add_argument("--search", help="Client name or estimate number")
    parser.add_argument("--max", type=int, help="Stop after this many estimates")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    params = {"approval": args.approval, "search": args.search, "limit": 100}
    write_rows(list(paginate("list_estimates", params, "estimates", args.max)), args.out)


if __name__ == "__main__":
    run(main)
