#!/usr/bin/env python3
"""Entry point for autoresearch dashboard server."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import uvicorn

from .app import create_app
from .state import DashboardState
from .watcher import start_periodic_rescan, start_watcher


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Autoresearch real-time monitoring dashboard")
    parser.add_argument(
        "--project",
        type=Path,
        default=Path.cwd(),
        help="Target project directory to watch (default: cwd)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=3847, help="Bind port")
    parser.add_argument(
        "--static",
        type=Path,
        default=None,
        help="Path to built React static files (default: dashboard/web/dist)",
    )
    args = parser.parse_args(argv)

    project = args.project.resolve()
    if not project.is_dir():
        print(f"Error: project path does not exist: {project}", file=sys.stderr)
        return 1

    dashboard_root = Path(__file__).resolve().parents[1]
    static_dir = args.static
    if static_dir is None:
        static_dir = dashboard_root / "web" / "dist"

    state = DashboardState(project)
    observer = start_watcher(state)
    start_periodic_rescan(state)

    app = create_app(state, static_dir=static_dir if static_dir.exists() else None)

    try:
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    finally:
        observer.stop()
        observer.join(timeout=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
