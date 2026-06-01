#!/usr/bin/env python3
"""Find a Lumenstone record by business code, name, or other field."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BASE = "http://localhost:8000/api/v1"

COLLECTIONS = {
    "employees": ("employees", "employee_id"),
    "employee": ("employees", "employee_id"),
    "products": ("products", "product_id"),
    "product": ("products", "product_id"),
    "shoppers": ("shoppers", "customer_id"),
    "shopper": ("shoppers", "customer_id"),
    "customers": ("shoppers", "customer_id"),
    "customer": ("shoppers", "customer_id"),
    "transactions": ("transactions", "transaction_id"),
    "transaction": ("transactions", "transaction_id"),
}

# Dedicated lookup endpoints for common fields
LOOKUP_ENDPOINTS = {
    "employees": {
        "employee_id": "by-employee-id",
        "name": "by-name",
    },
    "products": {
        "product_id": "by-product-id",
        "name": "by-name",
    },
    "shoppers": {
        "customer_id": "by-customer-id",
        "name": "by-name",
    },
    "transactions": {
        "transaction_id": "by-transaction-id",
    },
}


def fetch_json(url: str) -> object:
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find a Lumenstone record by business code or other field.",
    )
    parser.add_argument(
        "collection",
        choices=sorted(COLLECTIONS),
        help="Resource type to search",
    )
    parser.add_argument("--by", required=True, help="JSON field to match (e.g. name, employee_id)")
    parser.add_argument("--value", required=True, help="Exact value to match")
    parser.add_argument("--limit", type=int, default=500, help="Max list items to scan")
    parser.add_argument(
        "--detail",
        action="store_true",
        help="Fetch GET /{collection}/{id} for full nested payload",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("LUMENSTONE_API_URL", DEFAULT_BASE),
    )
    args = parser.parse_args()

    path, _default_field = COLLECTIONS[args.collection]
    base = args.base_url.rstrip("/")

    # Try dedicated lookup endpoint first for known fields
    lookup = LOOKUP_ENDPOINTS.get(path, {}).get(args.by)
    if lookup:
        lookup_url = f"{base}/{path}/{lookup}/{urllib.parse.quote(args.value, safe='')}"
        try:
            match = fetch_json(lookup_url)
            if match and (not isinstance(match, list) or match):
                json.dump(match, sys.stdout, indent=2)
                sys.stdout.write("\n")
                return
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                print(f"error: {exc}", file=sys.stderr)
                raise SystemExit(1) from exc
        except urllib.error.URLError as exc:
            print(f"error: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc

    # Fall back to listing and scanning
    list_url = f"{base}/{path}?{urllib.parse.urlencode({'limit': args.limit})}"

    try:
        items = fetch_json(list_url)
    except urllib.error.URLError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    if not isinstance(items, list):
        print("error: expected list response", file=sys.stderr)
        raise SystemExit(1)

    match = next(
        (row for row in items if str(row.get(args.by)) == args.value),
        None,
    )
    if match is None:
        print(
            f"error: no {path} with {args.by}={args.value!r}",
            file=sys.stderr,
        )
        raise SystemExit(1)

    if args.detail and "id" in match:
        try:
            match = fetch_json(f"{base}/{path}/{match['id']}")
        except urllib.error.URLError as exc:
            print(f"error: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc

    json.dump(match, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
