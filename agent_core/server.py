"""Web server for the OpenAI Agents SDK skill agent chat UI."""

from __future__ import annotations

import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .paths import REPO_ROOT, TRACE_LOG, WEB_DIR, default_skill_roots
from .registry import SkillRegistry
from .runner import GEMMA4_MODEL, SkillAgentRunner

runner: Optional[SkillAgentRunner] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global runner
    runner = SkillAgentRunner(verbose=False, log_enabled=True)
    yield
    if runner is not None:
        runner.close()


app = FastAPI(title="Gemma 4 Skill Agent Chat", lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: Optional[str] = None
    task: Optional[str] = None
    think: bool = True


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    turns: List[Dict[str, Any]]
    agent_id: Optional[str] = None
    run_id: Optional[str] = None


class ResetRequest(BaseModel):
    session_id: str


def _list_tasks() -> list[str]:
    tasks_dir = REPO_ROOT / "tasks"
    if not tasks_dir.is_dir():
        return []
    return sorted(
        path.name
        for path in tasks_dir.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    )


@app.get("/api/tasks")
def tasks() -> dict[str, list[str]]:
    return {"tasks": _list_tasks()}


@app.get("/api/skills")
def skills(task: Optional[str] = None) -> dict[str, Any]:
    if task:
        task_skills = REPO_ROOT / "tasks" / task / "skills"
        roots = [task_skills] if task_skills.is_dir() else list(default_skill_roots())
    else:
        roots = list(default_skill_roots())
    registry = SkillRegistry(*roots)
    return {
        "task": task,
        "skill_roots": [str(root) for root in registry.roots],
        "skills": [
            {
                "name": s.name,
                "description": s.description,
                "scripts": s.scripts,
                "path": str(s.path),
            }
            for s in registry.skills
        ],
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "model": GEMMA4_MODEL,
        "runtime": "openai-agents-sdk",
        "trace_log": str(TRACE_LOG),
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(body: ChatRequest) -> ChatResponse:
    if runner is None:
        raise HTTPException(status_code=503, detail="Agent runner not initialized")

    session_id = body.session_id or str(uuid.uuid4())

    try:
        result = runner.run(
            body.message.strip(), session_id=session_id, task=body.task, think=body.think
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if result.status == "error" and result.answer.startswith("Error:"):
        raise HTTPException(status_code=502, detail=result.answer)

    return ChatResponse(
        session_id=session_id,
        answer=result.answer,
        turns=result.turns,
        agent_id=result.agent_id,
        run_id=result.run_id,
    )


async def _stream_chat_events(
    message: str,
    session_id: str,
    task: Optional[str] = None,
    think: bool = True,
) -> AsyncIterator[str]:
    if runner is None:
        payload = {"phase": "error", "data": {"error": "Agent runner not initialized"}}
        yield f"data: {json.dumps(payload)}\n\n"
        return

    async for event in runner.run_stream(message, session_id=session_id, task=task, think=think):
        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0)


@app.post("/api/chat/stream")
async def chat_stream(body: ChatRequest) -> StreamingResponse:
    if runner is None:
        raise HTTPException(status_code=503, detail="Agent runner not initialized")

    session_id = body.session_id or str(uuid.uuid4())

    async def event_generator() -> AsyncIterator[str]:
        yield f"data: {json.dumps({'phase': 'session', 'data': {'session_id': session_id}}, ensure_ascii=False)}\n\n"
        async for chunk in _stream_chat_events(body.message.strip(), session_id, body.task, body.think):
            yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/reset")
def reset(body: ResetRequest) -> dict[str, bool]:
    if runner is None:
        raise HTTPException(status_code=503, detail="Agent runner not initialized")
    runner.clear_session(body.session_id)
    return {"ok": True}


@app.get("/")
def index() -> FileResponse:
    index_path = WEB_DIR / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=404, detail="Chat UI not found")
    return FileResponse(index_path)


if WEB_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="Gemma 4 Skill Agent Chat API")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8766, help="Bind port")
    args = parser.parse_args()

    uvicorn.run("agent_core.server:app", host=args.host, port=args.port, reload=False)
