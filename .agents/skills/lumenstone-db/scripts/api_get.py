#!/usr/bin/env python3
"""GET a Lumenstone API path and print JSON to stdout."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BASE = "http://localhost:8000/api/v1"


def main() -> None:
    parser = argparse.ArgumentParser(description="GET Lumenstone API resource.")
    parser.add_argument(
        "path",
        help="API path, e.g. employees or /analytics/top-customers",
    )
    parser.add_argument(
        "--query",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Query parameter (repeatable)",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("LUMENSTONE_API_URL", DEFAULT_BASE),
        help="API base URL without trailing slash",
    )
    args = parser.parse_args()

    raw_path = args.path if args.path.startswith("/") else f"/{args.path}"
    base = args.base_url.rstrip("/")

    # URL-encode the path so spaces and special characters don't crash the request.
    # e.g. "Devon Park" → "%2FDevon%20Park", which will produce a clean 404 instead of InvalidURL.
    encoded_path = urllib.parse.quote(raw_path, safe="/")
    url = f"{base}{encoded_path}"

    if args.query:
        params = urllib.parse.urlencode(
            [tuple(pair.split("=", 1)) for pair in args.query],
            doseq=True,
        )
        url = f"{url}?{params}"

    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.URLError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        sys.stdout.write(body)
        if not body.endswith("\n"):
            sys.stdout.write("\n")
        return

    json.dump(data, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
