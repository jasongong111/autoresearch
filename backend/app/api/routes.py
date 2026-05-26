"""FastAPI routers for autoresearch dashboard and orchestrator."""

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncGenerator, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse

from backend.app.api.events import EventBus
from backend.app.core.skills import discover_skills, read_skill_content
from backend.app.core.state import DashboardState
from backend.app.orchestrator.manager import RunManager
from backend.app.orchestrator.models import RunConfig, RunInstance


def make_health_router(state: DashboardState) -> APIRouter:
    router = APIRouter()

    @router.get("/api/health")
    def health() -> dict:
        return {
            "status": "ok",
            "project": str(state.project_root),
            "runCount": len(state.runs),
            "projectCount": len(state.projects),
            "activeRunId": state.active_run_id,
            "conversationCount": len(state.get_conversations()),
            "transcriptDirs": [str(d) for d in state.transcript_dirs],
        }

    return router


def make_projects_router(state: DashboardState) -> APIRouter:
    router = APIRouter()

    @router.get("/api/projects")
    def list_projects() -> dict:
        return {
            "projects": [p.to_dict() for p in state.projects],
        }

    return router


def make_runs_router(state: DashboardState) -> APIRouter:
    router = APIRouter()

    @router.get("/api/runs")
    def list_runs() -> dict:
        return {
            "runs": [r.to_dict() for r in state.runs],
            "projects": [p.to_dict() for p in state.projects],
            "activeRunId": state.active_run_id,
        }

    @router.get("/api/runs/{run_id:path}")
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

    @router.get("/api/runs/{run_id:path}/iterations")
    def get_iterations(run_id: str) -> dict:
        if not state.get_run(run_id):
            raise HTTPException(404, f"Run not found: {run_id}")
        return {"iterations": state.get_iterations(run_id)}

    @router.get("/api/runs/{run_id:path}/summary")
    def get_summary(run_id: str) -> dict:
        if not state.get_run(run_id):
            raise HTTPException(404, f"Run not found: {run_id}")
        return state.get_summary(run_id)

    @router.get("/api/runs/{run_id:path}/trace")
    def get_run_trace(run_id: str) -> dict:
        if not state.get_run(run_id):
            raise HTTPException(404, f"Run not found: {run_id}")
        return {"events": state.get_run_trace(run_id)}

    @router.get("/api/runs/{run_id:path}/gemma4-trace")
    def get_run_gemma4_trace(run_id: str) -> dict:
        if not state.get_run(run_id):
            raise HTTPException(404, f"Run not found: {run_id}")
        return {"events": state.get_run_gemma4_trace(run_id)}

    @router.get("/api/runs/{run_id:path}/gemma3-trace")
    def get_run_gemma3_trace(run_id: str) -> dict:
        if not state.get_run(run_id):
            raise HTTPException(404, f"Run not found: {run_id}")
        return {"events": state.get_run_gemma3_trace(run_id)}

    @router.get("/api/runs/{run_id:path}/analytics")
    def get_run_analytics(run_id: str) -> dict:
        if not state.get_run(run_id):
            raise HTTPException(404, f"Run not found: {run_id}")
        return state.get_run_analytics(run_id)

    @router.get("/api/runs/{run_id:path}/artifacts")
    def get_run_artifacts(run_id: str) -> dict:
        if not state.get_run(run_id):
            raise HTTPException(404, f"Run not found: {run_id}")
        return {"artifacts": state.get_run_artifacts(run_id)}

    @router.get("/api/runs/{run_id:path}/experiments")
    def get_run_experiments(run_id: str) -> dict:
        if not state.get_run(run_id):
            raise HTTPException(404, f"Run not found: {run_id}")
        return {"experiments": state.get_run_experiments(run_id)}

    @router.get("/api/trace")
    def get_trace() -> dict:
        state.refresh_runs()
        return {"events": state.get_trace()}

    @router.get("/api/analytics")
    def get_analytics() -> dict:
        state.refresh_runs()
        return state.get_analytics()

    @router.get("/api/experiments")
    def get_experiments() -> dict:
        state.refresh_runs()
        return {"experiments": state.get_experiments()}

    return router


def make_conversations_router(state: DashboardState) -> APIRouter:
    router = APIRouter()

    @router.get("/api/conversations")
    def list_conversations() -> dict:
        return {
            "conversations": state.get_conversations(),
            "transcriptDirs": [str(d) for d in state.transcript_dirs],
        }

    @router.get("/api/conversations/{conversation_id:path}/turns")
    def get_conversation_turns(conversation_id: str) -> dict:
        conv = state.get_conversation(conversation_id)
        if not conv:
            raise HTTPException(404, f"Conversation not found: {conversation_id}")
        return {
            "conversation": conv,
            "turns": state.get_conversation_turns(conversation_id),
        }

    return router


def make_git_router(state: DashboardState) -> APIRouter:
    router = APIRouter()

    @router.get("/api/git/commits")
    def git_commits(project_id: Optional[str] = None) -> dict:
        state.refresh_git()
        return {"commits": state.get_git_commits(project_id)}

    @router.get("/api/git/commits/{commit_hash}/stat")
    def git_commit_stat(commit_hash: str, project_id: Optional[str] = None) -> dict:
        stat = state.get_commit_stat(commit_hash, project_id)
        if stat is None:
            raise HTTPException(404, "Commit not found or git unavailable")
        return {"hash": commit_hash, "stat": stat}

    return router


def make_skills_router(state: DashboardState) -> APIRouter:
    router = APIRouter()

    @router.get("/api/skills")
    def list_skills() -> dict:
        from backend.app.core.skills import discover_skills

        docs = discover_skills(state.project_root)
        return {"skills": [d.to_dict() for d in docs]}

    @router.get("/api/skills/{doc_id:path}")
    def get_skill(doc_id: str) -> dict:
        from backend.app.core.skills import read_skill_content

        content = read_skill_content(state.project_root, doc_id)
        if content is None:
            raise HTTPException(404, f"Skill doc not found: {doc_id}")
        return {"id": doc_id, "content": content}

    return router


def make_events_router(event_bus: EventBus) -> APIRouter:
    router = APIRouter()

    @router.get("/api/events")
    async def events(request: Request) -> StreamingResponse:
        queue = event_bus.subscribe()

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
                event_bus.unsubscribe(queue)

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return router


def make_orchestrator_router(manager: RunManager) -> APIRouter:
    router = APIRouter()

    @router.post("/api/orchestrator/configs")
    def create_config(data: Dict[str, Any]) -> dict:
        config = manager.create_config(**data)
        return config.model_dump(mode="json")

    @router.get("/api/orchestrator/configs")
    def list_configs() -> dict:
        return {"configs": [c.model_dump(mode="json") for c in manager.list_configs()]}

    @router.get("/api/orchestrator/configs/{config_id}")
    def get_config(config_id: str) -> dict:
        config = manager.get_config(config_id)
        if config is None:
            raise HTTPException(404, f"Config not found: {config_id}")
        return config.model_dump(mode="json")

    @router.put("/api/orchestrator/configs/{config_id}")
    def update_config(config_id: str, data: Dict[str, Any]) -> dict:
        config = manager.update_config(config_id, **data)
        if config is None:
            raise HTTPException(404, f"Config not found: {config_id}")
        return config.model_dump(mode="json")

    @router.delete("/api/orchestrator/configs/{config_id}")
    def delete_config(config_id: str) -> dict:
        ok = manager.delete_config(config_id)
        if not ok:
            raise HTTPException(404, f"Config not found: {config_id}")
        return {"deleted": True}

    @router.post("/api/orchestrator/configs/{config_id}/start")
    def start_run(config_id: str) -> dict:
        instance = manager.start_run(config_id)
        if instance is None:
            raise HTTPException(404, f"Config not found: {config_id}")
        return instance.model_dump(mode="json")

    @router.get("/api/orchestrator/instances")
    def list_instances() -> dict:
        return {"instances": [i.model_dump(mode="json") for i in manager.list_instances()]}

    @router.get("/api/orchestrator/instances/{instance_id}")
    def get_instance(instance_id: str) -> dict:
        instance = manager.get_instance(instance_id)
        if instance is None:
            raise HTTPException(404, f"Instance not found: {instance_id}")
        return instance.model_dump(mode="json")

    @router.post("/api/orchestrator/instances/{instance_id}/stop")
    def stop_run(instance_id: str) -> dict:
        ok = manager.stop_run(instance_id)
        if not ok:
            raise HTTPException(404, f"Instance not found or not running: {instance_id}")
        return {"stopped": True}

    @router.get("/api/orchestrator/instances/{instance_id}/logs")
    def get_instance_logs(instance_id: str) -> dict:
        instance = manager.get_instance(instance_id)
        if instance is None:
            raise HTTPException(404, f"Instance not found: {instance_id}")
        return {
            "stdout": instance.stdout_tail,
            "stderr": instance.stderr_tail,
        }

    @router.post("/api/orchestrator/configs/validate")
    def validate_config(data: Dict[str, Any]) -> dict:
        """Dry-run the verify command and return whether it outputs a number."""
        import re
        import subprocess

        verify = data.get("verify", "")
        if not verify:
            return {"valid": False, "error": "No verify command provided"}

        project_path = data.get("project_path", ".")
        try:
            result = subprocess.run(
                verify,
                shell=True,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            return {"valid": False, "error": "Verify command timed out after 30s"}
        except Exception as exc:
            return {"valid": False, "error": str(exc)}

        output = result.stdout + result.stderr
        # Look for a number (integer or float) in the output
        numbers = re.findall(r"\b\d+(?:\.\d+)?\b", output)
        if numbers:
            return {"valid": True, "numbers": numbers, "exitCode": result.returncode}
        return {"valid": False, "error": "Verify command did not output a parseable number", "output": output, "exitCode": result.returncode}

    return router
