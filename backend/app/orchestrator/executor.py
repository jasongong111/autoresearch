"""Subprocess executor for autoresearch runs."""

from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path
from typing import Optional

from .models import RunConfig, RunInstance


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
    }
    (autoresearch_dir / "session.json").write_text(
        json.dumps(session, indent=2), encoding="utf-8"
    )


def _build_claude_invocation(config: RunConfig) -> list[str]:
    """Build a command list for the Claude Code CLI."""
    prompt_lines = [f"Use the installed `autoresearch` skill."]
    cmd = config.command.replace("autoresearch:", "/autoresearch:")
    prompt_lines.append(cmd)

    if config.goal:
        prompt_lines.append(f"Goal: {config.goal}")
    if config.scope:
        prompt_lines.append(f"Scope: {config.scope}")
    if config.metric:
        prompt_lines.append(f"Metric: {config.metric}")
    if config.verify:
        prompt_lines.append(f"Verify: {config.verify}")
    if config.guard:
        prompt_lines.append(f"Guard: {config.guard}")
    if config.direction:
        prompt_lines.append(f"Direction: {config.direction}")
    if config.iterations is not None:
        prompt_lines.append(f"Iterations: {config.iterations}")

    for flag, value in config.flags.items():
        if isinstance(value, bool) and value:
            prompt_lines.append(f"{flag}")
        else:
            prompt_lines.append(f"{flag}: {value}")

    prompt = "\n".join(prompt_lines)
    return ["claude", "-p", prompt]


def _build_codex_invocation(config: RunConfig) -> list[str]:
    """Build a command list for the Codex CLI via the autoresearch wrapper."""
    tokens = [config.command]
    for flag, value in config.flags.items():
        if isinstance(value, bool) and value:
            tokens.append(flag)
        else:
            tokens.extend([flag, str(value)])

    prose_parts: list[str] = []
    if config.goal:
        prose_parts.append(f"Goal: {config.goal}")
    if config.scope:
        prose_parts.append(f"Scope: {config.scope}")
    if config.metric:
        prose_parts.append(f"Metric: {config.metric}")
    if config.verify:
        prose_parts.append(f"Verify: {config.verify}")
    if config.guard:
        prose_parts.append(f"Guard: {config.guard}")
    if config.direction:
        prose_parts.append(f"Direction: {config.direction}")
    if config.iterations is not None:
        prose_parts.append(f"Iterations: {config.iterations}")

    if prose_parts:
        tokens.append("--")
        tokens.extend(prose_parts)

    # Invoke via the local autoresearch CLI wrapper
    return ["python3", "-m", "plugins.autoresearch.scripts.autoresearch_cli", *tokens]


def _build_opencode_invocation(config: RunConfig) -> list[str]:
    """Build a command list for OpenCode.

    OpenCode uses underscore naming: ``/autoresearch_plan`` instead of ``/autoresearch:plan``.
    """
    cmd = config.command.replace("autoresearch:", "/autoresearch_")
    prompt_lines = [cmd]

    if config.goal:
        prompt_lines.append(f"Goal: {config.goal}")
    if config.scope:
        prompt_lines.append(f"Scope: {config.scope}")
    if config.metric:
        prompt_lines.append(f"Metric: {config.metric}")
    if config.verify:
        prompt_lines.append(f"Verify: {config.verify}")
    if config.guard:
        prompt_lines.append(f"Guard: {config.guard}")
    if config.direction:
        prompt_lines.append(f"Direction: {config.direction}")
    if config.iterations is not None:
        prompt_lines.append(f"Iterations: {config.iterations}")

    for flag, value in config.flags.items():
        if isinstance(value, bool) and value:
            prompt_lines.append(f"{flag}")
        else:
            prompt_lines.append(f"{flag}: {value}")

    prompt = "\n".join(prompt_lines)
    return ["opencode", "-p", prompt]


def spawn_run(instance: RunInstance, config: RunConfig) -> Optional[subprocess.Popen]:
    """Spawn the runner subprocess and return the Popen handle."""
    project_path = Path(config.project_path).resolve()
    if not project_path.is_dir():
        raise FileNotFoundError(f"Project path does not exist: {config.project_path}")

    _write_session_json(project_path, config)

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
