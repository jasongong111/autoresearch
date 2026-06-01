#!/usr/bin/env python3
"""Parse a single numeric metric from verify command stdout."""

from __future__ import annotations

import re


def parse_metric(stdout: str) -> float:
    """Return the metric printed by a verify script (last parseable float line in stdout)."""
    lines = [ln.strip() for ln in stdout.strip().splitlines() if ln.strip()]
    for line in reversed(lines):
        try:
            return float(line)
        except ValueError:
            match = re.fullmatch(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", line)
            if match:
                return float(match.group(0))
    raise ValueError(
        "Verify stdout did not end with a numeric metric. "
        f"Last lines: {lines[-3:] if lines else '(empty)'}"
    )
