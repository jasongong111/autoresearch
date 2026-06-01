"""Shared autoresearch prompt builders for agent runners."""

from __future__ import annotations

from typing import Any

from .models import RunConfig


def autoresearch_config_lines(config: RunConfig) -> list[str]:
    """Prose configuration lines shared across prompt-based runners."""
    lines: list[str] = []
    if config.goal:
        lines.append(f"Goal: {config.goal}")
    if config.scope:
        lines.append(f"Scope: {config.scope}")
    if config.metric:
        lines.append(f"Metric: {config.metric}")
    if config.verify:
        lines.append(f"Verify: {config.verify}")
    if config.guard:
        lines.append(f"Guard: {config.guard}")
    if config.direction:
        lines.append(f"Direction: {config.direction}")
    if config.iterations is not None:
        lines.append(f"Iterations: {config.iterations}")
    for flag, value in config.flags.items():
        if flag == "model":
            continue
        if isinstance(value, bool) and value:
            lines.append(f"{flag}")
        else:
            lines.append(f"{flag}: {value}")
    return lines


def build_claude_prompt(config: RunConfig) -> str:
    prompt_lines = ["Use the installed `autoresearch` skill."]
    cmd = config.command.replace("autoresearch:", "/autoresearch:")
    prompt_lines.append(cmd)
    prompt_lines.extend(autoresearch_config_lines(config))
    return "\n".join(prompt_lines)


def build_cursor_prompt(config: RunConfig) -> str:
    prompt_lines = [
        "Read and follow the project skill at `.agents/skills/autoresearch/SKILL.md` "
        "and its `references/` files. This is a BLOCKING skill invocation — "
        "load it before any other action.",
    ]
    cmd = config.command.replace("autoresearch:", "/autoresearch:")
    prompt_lines.append(cmd)
    prompt_lines.extend(autoresearch_config_lines(config))
    return "\n".join(prompt_lines)


def build_opencode_prompt(config: RunConfig) -> str:
    cmd = config.command.replace("autoresearch:", "/autoresearch_")
    prompt_lines = [cmd]
    prompt_lines.extend(autoresearch_config_lines(config))
    return "\n".join(prompt_lines)


def build_codex_argv(config: RunConfig) -> list[str]:
    """Build argv for the Codex autoresearch wrapper CLI."""
    tokens = [config.command]
    for flag, value in config.flags.items():
        if flag == "model":
            continue
        if isinstance(value, bool) and value:
            tokens.append(flag)
        else:
            tokens.extend([flag, str(value)])

    prose = autoresearch_config_lines(config)
    if prose:
        tokens.append("--")
        tokens.extend(prose)

    return ["python3", "-m", "plugins.autoresearch.scripts.autoresearch_cli", *tokens]


def cursor_model(config: RunConfig) -> str:
    import os

    model = config.flags.get("model")
    if isinstance(model, str) and model.strip():
        return model.strip()
    env_model = os.environ.get("CURSOR_MODEL", "").strip()
    if env_model:
        return env_model
    return "composer-2.5"
