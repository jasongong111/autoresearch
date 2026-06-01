"""Subprocess executor for autoresearch runs."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Optional

from .models import RunConfig, RunInstance
from .prompt import build_claude_prompt, build_codex_argv, build_opencode_prompt


def _write_session_json(project_path: Path, config: RunConfig) -> None:
    """Write a session.json so the dashboard picks up the run immediately."""
    autoresearch_dir = project_path / ".autoresearch"
    autoresearch_dir.mkdir(parents=True, exist_ok=True)
    session = {
        "command": config.command,
        "goal": config.goal,
        "scope": config.scope,
        "metric": config.metric,
        "verify": config.verify,
        "guard": config.guard,
        "direction": config.direction,
        "iterations": config.iterations,
        "runner": config.runner,
    }
    (autoresearch_dir / "session.json").write_text(
        json.dumps(session, indent=2), encoding="utf-8"
    )


def _build_claude_invocation(config: RunConfig) -> list[str]:
    return ["claude", "-p", build_claude_prompt(config)]


def _build_codex_invocation(config: RunConfig) -> list[str]:
    return build_codex_argv(config)


def _build_opencode_invocation(config: RunConfig) -> list[str]:
    return ["opencode", "-p", build_opencode_prompt(config)]


def spawn_run(instance: RunInstance, config: RunConfig) -> Optional[subprocess.Popen]:
    """Spawn the runner subprocess and return the Popen handle.

    The cursor runner is in-process (Cursor SDK) and handled by RunManager.
    """
    project_path = Path(config.project_path).resolve()
    if not project_path.is_dir():
        raise FileNotFoundError(f"Project path does not exist: {config.project_path}")

    _write_session_json(project_path, config)

    if config.runner == "cursor":
        raise ValueError("cursor runner uses Cursor SDK in-process; call RunManager.start_cursor_run")

    if config.runner == "claude":
        cmd = _build_claude_invocation(config)
    elif config.runner == "codex":
        cmd = _build_codex_invocation(config)
    elif config.runner == "opencode":
        cmd = _build_opencode_invocation(config)
    else:
        raise ValueError(f"Unsupported runner: {config.runner}")

    return subprocess.Popen(
        cmd,
        cwd=str(project_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def prepare_run_workspace(config: RunConfig) -> Path:
    """Validate project path and write session metadata."""
    project_path = Path(config.project_path).resolve()
    if not project_path.is_dir():
        raise FileNotFoundError(f"Project path does not exist: {config.project_path}")
    _write_session_json(project_path, config)
    return project_path
