#!/usr/bin/env python3
"""Initialize a task folder for autoresearch.

Creates logs/, autoresearch-results.tsv, and runs the baseline verify command.

Usage:
    python init_task.py --verify ./verify.sh --direction higher

Optional:
    --guard ./scripts/check-guard.sh
    --selection-verify "./selection-verify.sh"
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_metric import parse_metric  # noqa: E402


def run(cmd: str) -> tuple[int, str, str]:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)
    return result.returncode, result.stdout, result.stderr


def init_tsv(direction: str, tsv_path: str = "autoresearch-results.tsv") -> None:
    dir_comment = f"# metric_direction: {direction}\n"
    header = "iteration\tcommit\tmetric\tdelta\tguard\tguard-metric\tstatus\tdescription\n"
    with open(tsv_path, "w") as f:
        f.write(dir_comment + header)


def metric_from_run(cmd: str) -> tuple[float, str]:
    code, stdout, stderr = run(cmd)
    if code != 0:
        raise RuntimeError(f"Command failed (exit {code}):\n{stderr or stdout}")
    try:
        return parse_metric(stdout), stdout
    except ValueError as exc:
        hint = ""
        if stderr.strip():
            hint = f"\n(stderr had {len(stderr.splitlines())} lines — metrics belong on stdout only)"
        raise RuntimeError(f"{exc}{hint}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize an autoresearch task folder.")
    parser.add_argument("--verify", required=True, help="Verify command that prints a single number")
    parser.add_argument("--direction", required=True, choices=["higher_is_better", "lower_is_better"])
    parser.add_argument("--guard", default=None, help="Optional guard command")
    parser.add_argument(
        "--selection-verify",
        default=None,
        help="Optional selection verify (e.g. ./selection-verify.sh)",
    )
    parser.add_argument("--tsv", default="autoresearch-results.tsv")
    args = parser.parse_args()

    os.makedirs("logs/agent-core", exist_ok=True)
    init_tsv(args.direction, tsv_path=args.tsv)

    print("Running baseline verify...")
    try:
        baseline, _ = metric_from_run(args.verify)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    guard_status = "-"
    guard_metric = None
    if args.guard:
        try:
            guard_metric, _ = metric_from_run(args.guard)
            guard_status = "pass"
        except RuntimeError:
            guard_status = "fail"

    selection_baseline = None
    if args.selection_verify:
        try:
            selection_baseline, _ = metric_from_run(args.selection_verify)
        except RuntimeError as exc:
            print(f"Selection verify failed: {exc}", file=sys.stderr)
            return 1

    result = subprocess.run("git rev-parse --short HEAD", shell=True, capture_output=True, text=True)
    commit = result.stdout.strip() if result.returncode == 0 else "-"

    with open(args.tsv, "a") as f:
        guard_metric_str = f"{guard_metric:.1f}" if guard_metric is not None else "-"
        f.write(
            f"0\t{commit}\t{baseline:.4f}\t0.0000\t{guard_status}\t{guard_metric_str}\t"
            f"baseline\tinitial state — metric {baseline}\n"
        )

    print(f"Baseline recorded: {baseline}")
    if selection_baseline is not None:
        print(f"Selection baseline: {selection_baseline}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
