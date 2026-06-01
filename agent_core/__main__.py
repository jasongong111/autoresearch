#!/usr/bin/env python3
"""CLI for the OpenAI Agents SDK skill agent."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from .log_format import format_events_text, load_trace_events
from .paths import TRACE_LOG
from .runner import SkillAgentRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skill-agent",
        description="Gemma 4 agent with dynamic skill discovery (OpenAI Agents SDK)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    chat = subparsers.add_parser("chat", help="Run a chat prompt or REPL")
    chat.add_argument("prompt", nargs="?", help="User message for a one-shot run")
    chat.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Start a multi-turn REPL session",
    )
    chat.add_argument(
        "--system",
        help="Optional base system prompt override (skill catalog is appended automatically)",
    )
    chat.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print tool trace to stderr",
    )
    chat.add_argument(
        "--task",
        help="Task name under tasks/<task>/skills (loads only that skill package)",
    )

    serve = subparsers.add_parser("serve", help="Start the web chat UI")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8766)

    logs = subparsers.add_parser("logs", help="Pretty-print the JSONL agent trace log")
    logs.add_argument(
        "--trace",
        type=str,
        default=str(TRACE_LOG),
        help=f"Path to trace JSONL (default: {TRACE_LOG})",
    )
    logs.add_argument("--session", help="Only show events for one session id")
    logs.add_argument(
        "--raw-stream",
        action="store_true",
        help="Do not collapse streaming token deltas",
    )
    logs.add_argument(
        "--tail",
        type=int,
        default=0,
        help="Only format the last N events",
    )

    return parser


def run_interactive(runner: SkillAgentRunner, task: Optional[str]) -> int:
    session_id = "cli"
    if task:
        print(f"Task skills: tasks/{task}/skills/", file=sys.stderr)
    print("Skill agent (interactive). Type 'exit' or Ctrl-D to quit.", file=sys.stderr)

    while True:
        try:
            user_input = input("you> ").strip()
        except EOFError:
            print(file=sys.stderr)
            return 0

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            return 0

        result = runner.run(user_input, session_id=session_id, task=task)
        print(result.answer)


def cmd_chat(args: argparse.Namespace) -> int:
    runner = SkillAgentRunner(
        system_prompt=args.system,
        verbose=args.verbose,
    )
    try:
        if args.interactive:
            return run_interactive(runner, args.task)

        if not args.prompt:
            print("error: provide a prompt or use --interactive", file=sys.stderr)
            return 2

        result = runner.run(args.prompt, task=args.task)
        print(result.answer)
        return 0 if result.answer and not result.answer.startswith("Error:") else 1
    finally:
        runner.close()


def cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    uvicorn.run(
        "agent_core.server:app",
        host=args.host,
        port=args.port,
        reload=False,
    )
    return 0


def cmd_logs(args: argparse.Namespace) -> int:
    from pathlib import Path

    trace_path = Path(args.trace)
    events = load_trace_events(trace_path, session_id=args.session)
    if args.tail:
        events = events[-args.tail :]

    if not events:
        print(f"No trace events found in {trace_path}", file=sys.stderr)
        return 1

    print(format_events_text(events, collapse_stream=not args.raw_stream))
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "chat":
        return cmd_chat(args)
    if args.command == "serve":
        return cmd_serve(args)
    if args.command == "logs":
        return cmd_logs(args)

    print(f"unknown command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
