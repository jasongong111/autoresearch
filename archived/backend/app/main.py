#!/usr/bin/env python3
"""Entry point for autoresearch web app server."""

from __future__ import annotations

import argparse
import asyncio
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.events import EventBus
from backend.app.api.routes import (
    make_conversations_router,
    make_events_router,
    make_git_router,
    make_health_router,
    make_orchestrator_router,
    make_projects_router,
    make_runs_router,
    make_skills_router,
)
from backend.app.core.state import DashboardState
from backend.app.core.watcher import (
    start_conversation_poll,
    start_periodic_rescan,
    start_transcript_watcher,
    start_watcher,
)
from backend.app.orchestrator.manager import RunManager


def create_app(
    state: DashboardState,
    event_bus: EventBus,
    run_manager: RunManager,
    static_dir: Path | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        loop = asyncio.get_running_loop()
        state.set_event_loop(loop)
        event_bus.set_event_loop(loop)
        state.refresh_runs()
        state.refresh_git(force=True)
        run_manager.start_polling()
        yield
        run_manager.stop_polling()

    app = FastAPI(title="Autoresearch", version="2.1.0", lifespan=lifespan)
    app.state.dashboard = state
    app.state.event_bus = event_bus
    app.state.run_manager = run_manager

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(make_health_router(state))
    app.include_router(make_projects_router(state))
    app.include_router(make_runs_router(state))
    app.include_router(make_conversations_router(state))
    app.include_router(make_git_router(state))
    app.include_router(make_events_router(event_bus))
    app.include_router(make_skills_router(state))
    app.include_router(make_orchestrator_router(run_manager))

    if static_dir and static_dir.exists():
        assets = static_dir / "assets"
        if assets.exists():
            app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

        @app.get("/")
        def index() -> FileResponse:
            index_file = static_dir / "index.html"
            if index_file.exists():
                return FileResponse(index_file)
            raise FileResponse("Dashboard UI not built. Run: cd frontend && npm run build")

    return app


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Autoresearch web app")
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
        help="Path to built React static files (default: frontend/dist)",
    )
    parser.add_argument(
        "--transcripts-dir",
        type=Path,
        action="append",
        default=None,
        help="Directory with agent conversation JSONL (repeatable). Auto-detects ~/.cursor/projects/.../agent-transcripts if omitted.",
    )
    args = parser.parse_args(argv)

    project = args.project.resolve()
    if not project.is_dir():
        print(f"Error: project path does not exist: {project}", file=sys.stderr)
        return 1

    repo_root = Path(__file__).resolve().parents[2]
    static_dir = args.static
    if static_dir is None:
        static_dir = repo_root / "frontend" / "dist"

    state = DashboardState(project, transcript_dirs=args.transcripts_dir)
    event_bus = EventBus()

    # Wire state to publish through the event bus
    original_schedule = state._schedule_publish

    def _publish_via_bus(event: dict) -> None:
        event_bus.schedule_publish(event)

    state._schedule_publish = _publish_via_bus  # type: ignore[method-assign]

    run_manager = RunManager(event_callback=_publish_via_bus, workspace_root=project)

    observer = start_watcher(state)
    transcript_observer = start_transcript_watcher(state)
    start_conversation_poll(state)
    start_periodic_rescan(state)

    app = create_app(
        state,
        event_bus,
        run_manager,
        static_dir=static_dir if static_dir.exists() else None,
    )

    try:
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    finally:
        observer.stop()
        observer.join(timeout=2)
        if transcript_observer is not None:
            transcript_observer.stop()
            transcript_observer.join(timeout=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
