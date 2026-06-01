#!/usr/bin/env python3
"""CLI entry point: run autoresearch with the Cursor SDK local agent."""

from __future__ import annotations

import argparse
import sys
import threading

from backend.app.orchestrator.cursor_runner import run_cursor_agent
from backend.app.orchestrator.executor import prepare_run_workspace
from backend.app.orchestrator.models import RunConfig


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run autoresearch via the Cursor SDK (local agent)."
    )
    parser.add_argument("--project", default=".", help="Target project directory")
    parser.add_argument(
        "--command",
        default="autoresearch",
        help="autoresearch subcommand (default: autoresearch)",
    )
    parser.add_argument("--goal", default="", help="Goal")
    parser.add_argument("--scope", default="", help="Scope globs")
    parser.add_argument("--metric", default="", help="Metric description")
    parser.add_argument("--verify", default="", help="Verify shell command")
    parser.add_argument("--guard", default="", help="Optional guard command")
    parser.add_argument(
        "--direction",
        default="higher",
        choices=["higher", "lower"],
        help="Metric direction",
    )
    parser.add_argument("--iterations", type=int, default=None, help="Bounded iteration count")
    parser.add_argument(
        "--model",
        default="composer-2.5",
        help="Cursor model id (default: composer-2.5)",
    )
    args = parser.parse_args()

    config = RunConfig(
        command=args.command,
        goal=args.goal,
        scope=args.scope,
        metric=args.metric,
        verify=args.verify,
        guard=args.guard or None,
        direction=args.direction,
        iterations=args.iterations,
        runner="cursor",
        project_path=args.project,
        flags={"model": args.model},
    )

    prepare_run_workspace(config)
    cancel = threading.Event()

    def on_line(stream: str, line: str) -> None:
        target = sys.stdout if stream == "stdout" else sys.stderr
        print(line, file=target, flush=True)

    exit_code, error = run_cursor_agent(config, on_line, cancel)
    if error:
        print(error, file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
