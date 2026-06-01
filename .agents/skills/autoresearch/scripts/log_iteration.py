#!/usr/bin/env python3
"""Append an iteration record to the TSV results log and NDJSON experiment log.

Usage:
    python log_iteration.py \
        --iteration 1 \
        --commit b2c3d4e \
        --metric 0.65 \
        --delta 0.05 \
        --guard pass \
        --status keep \
        --description "add API routing rules"

Optional:
    --guard-metric 48200
    --hypothesis "routing rules reduce tool ambiguity"
    --files-read skills/qa/SKILL.md \
    --files-modified skills/qa/SKILL.md \
    --verify-output "last 500 chars..."
    --duration-ms 42000
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone


def append_tsv(
    iteration: int,
    commit: str,
    metric: float | None,
    delta: float | None,
    guard: str,
    guard_metric: float | None,
    status: str,
    description: str,
    tsv_path: str = "autoresearch-results.tsv",
) -> None:
    row = [
        str(iteration),
        commit if commit else "-",
        f"{metric:.4f}" if metric is not None else "-",
        f"{delta:+.4f}" if delta is not None else "-",
        guard if guard else "-",
        f"{guard_metric:.1f}" if guard_metric is not None else "-",
        status,
        description,
    ]
    with open(tsv_path, "a") as f:
        f.write("\t".join(row) + "\n")


def append_ndjson(
    iteration: int,
    commit: str,
    metric: float | None,
    delta: float | None,
    guard: str,
    guard_metric: float | None,
    status: str,
    description: str,
    hypothesis: str | None,
    files_read: list[str],
    files_modified: list[str],
    verify_output: str | None,
    duration_ms: int | None,
    ndjson_path: str = "logs/experiment.jsonl",
) -> None:
    os.makedirs(os.path.dirname(ndjson_path) or ".", exist_ok=True)
    record = {
        "iteration": iteration,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": status,
        "commit": commit if commit else "-",
        "metric": metric,
        "delta": delta,
        "guard": guard if guard else "-",
        "description": description,
    }
    if guard_metric is not None:
        record["guardMetric"] = guard_metric
    if hypothesis:
        record["hypothesis"] = hypothesis
    if files_read:
        record["filesRead"] = files_read
    if files_modified:
        record["filesModified"] = files_modified
    if verify_output:
        record["verifyOutput"] = verify_output[-500:]
    if duration_ms is not None:
        record["durationMs"] = duration_ms

    with open(ndjson_path, "a") as f:
        f.write(json.dumps(record, separators=(",", ":")) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Log an autoresearch iteration.")
    parser.add_argument("--iteration", type=int, required=True)
    parser.add_argument("--commit", default="-")
    parser.add_argument("--metric", type=float, default=None)
    parser.add_argument("--delta", type=float, default=None)
    parser.add_argument("--guard", default="-")
    parser.add_argument("--guard-metric", type=float, default=None)
    parser.add_argument("--status", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--hypothesis", default=None)
    parser.add_argument("--files-read", nargs="*", default=[])
    parser.add_argument("--files-modified", nargs="*", default=[])
    parser.add_argument("--verify-output", default=None)
    parser.add_argument("--duration-ms", type=int, default=None)
    parser.add_argument("--tsv", default="autoresearch-results.tsv")
    parser.add_argument("--ndjson", default="logs/experiment.jsonl")
    args = parser.parse_args()

    append_tsv(
        args.iteration,
        args.commit,
        args.metric,
        args.delta,
        args.guard,
        args.guard_metric,
        args.status,
        args.description,
        tsv_path=args.tsv,
    )
    append_ndjson(
        args.iteration,
        args.commit,
        args.metric,
        args.delta,
        args.guard,
        args.guard_metric,
        args.status,
        args.description,
        args.hypothesis,
        args.files_read,
        args.files_modified,
        args.verify_output,
        args.duration_ms,
        ndjson_path=args.ndjson,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
