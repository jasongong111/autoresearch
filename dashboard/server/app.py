"""FastAPI application for autoresearch dashboard."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .state import DashboardState


def create_app(state: DashboardState, static_dir: Optional[Path] = None) -> FastAPI:
    app = FastAPI(title="Autoresearch Dashboard", version="1.0.0")
    app.state.dashboard = state
    app.state.loop: Optional[asyncio.AbstractEventLoop] = None

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def startup() -> None:
        app.state.loop = asyncio.get_running_loop()
        state.set_event_loop(app.state.loop)
        state.refresh_runs()
        state.refresh_git(force=True)

    @app.get("/api/health")
    def health() -> dict:
        return {
            "status": "ok",
            "project": str(state.project_root),
            "runCount": len(state.runs),
            "activeRunId": state.active_run_id,
            "conversationCount": len(state.get_conversations()),
            "transcriptDirs": [str(d) for d in state.transcript_dirs],
        }

    @app.get("/api/runs")
    def list_runs() -> dict:
        return {
            "runs": [r.to_dict() for r in state.runs],
            "activeRunId": state.active_run_id,
        }

    @app.get("/api/runs/{run_id:path}/iterations")
    def get_iterations(run_id: str) -> dict:
        if not state.get_run(run_id):
            raise HTTPException(404, f"Run not found: {run_id}")
        return {"iterations": state.get_iterations(run_id)}

    @app.get("/api/runs/{run_id:path}/summary")
    def get_summary(run_id: str) -> dict:
        if not state.get_run(run_id):
            raise HTTPException(404, f"Run not found: {run_id}")
        return state.get_summary(run_id)

    @app.get("/api/trace")
    def get_trace() -> dict:
        state.refresh_runs()
        return {"events": state.get_trace()}

    @app.get("/api/analytics")
    def get_analytics() -> dict:
        state.refresh_runs()
        return state.get_analytics()

    @app.get("/api/runs/{run_id:path}/trace")
    def get_run_trace(run_id: str) -> dict:
        if not state.get_run(run_id):
            raise HTTPException(404, f"Run not found: {run_id}")
        return {"events": state.get_run_trace(run_id)}

    @app.get("/api/runs/{run_id:path}/analytics")
    def get_run_analytics(run_id: str) -> dict:
        if not state.get_run(run_id):
            raise HTTPException(404, f"Run not found: {run_id}")
        return state.get_run_analytics(run_id)

    @app.get("/api/conversations")
    def list_conversations() -> dict:
        return {
            "conversations": state.get_conversations(),
            "transcriptDirs": [str(d) for d in state.transcript_dirs],
        }

    @app.get("/api/conversations/{conversation_id:path}/turns")
    def get_conversation_turns(conversation_id: str) -> dict:
        conv = state.get_conversation(conversation_id)
        if not conv:
            raise HTTPException(404, f"Conversation not found: {conversation_id}")
        return {
            "conversation": conv,
            "turns": state.get_conversation_turns(conversation_id),
        }

    @app.get("/api/runs/{run_id:path}/artifacts")
    def get_run_artifacts(run_id: str) -> dict:
        if not state.get_run(run_id):
            raise HTTPException(404, f"Run not found: {run_id}")
        return {"artifacts": state.get_run_artifacts(run_id)}

    @app.get("/api/runs/{run_id:path}")
    def get_run(run_id: str) -> dict:
        run = state.get_run(run_id)
        if not run:
            raise HTTPException(404, f"Run not found: {run_id}")
        session = state.get_run_session(run_id)
        return {
            **run.to_dict(),
            "session": session,
            "isActive": run_id == state.active_run_id,
        }

    @app.get("/api/git/commits")
    def git_commits() -> dict:
        state.refresh_git()
        return {"commits": state.get_git_commits()}

    @app.get("/api/git/commits/{commit_hash}/stat")
    def git_commit_stat(commit_hash: str) -> dict:
        stat = state.get_commit_stat(commit_hash)
        if stat is None:
            raise HTTPException(404, "Commit not found or git unavailable")
        return {"hash": commit_hash, "stat": stat}

    @app.get("/api/events")
    async def events(request: Request) -> StreamingResponse:
        queue = state.subscribe()

        async def stream() -> AsyncGenerator[str, None]:
            try:
                yield f"data: {json.dumps({'type': 'connected'})}\n\n"
                while True:
                    if await request.is_disconnected():
                        break
                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=15.0)
                        yield f"data: {json.dumps(event)}\n\n"
                    except asyncio.TimeoutError:
                        yield ": keepalive\n\n"
            finally:
                state.unsubscribe(queue)

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    if static_dir and static_dir.exists():
        assets = static_dir / "assets"
        if assets.exists():
            app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

        @app.get("/")
        def index() -> FileResponse:
            index_file = static_dir / "index.html"
            if index_file.exists():
                return FileResponse(index_file)
            raise HTTPException(404, "Dashboard UI not built. Run: cd dashboard/web && npm run build")

    return app
