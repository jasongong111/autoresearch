"""Tests for orchestrator prompt builders and Cursor SDK runner."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest

from backend.app.orchestrator.models import RunConfig
from backend.app.orchestrator.prompt import (
    build_claude_prompt,
    build_cursor_prompt,
    cursor_model,
)
from backend.app.orchestrator.cursor_runner import run_cursor_agent


def test_build_cursor_prompt_includes_skill_and_config() -> None:
    config = RunConfig(
        command="autoresearch",
        goal="Improve score",
        scope="skills/**",
        metric="accuracy",
        verify="./tests/verify-metric.sh",
        iterations=3,
    )
    prompt = build_cursor_prompt(config)
    assert ".agents/skills/autoresearch/SKILL.md" in prompt
    assert "Goal: Improve score" in prompt
    assert "Iterations: 3" in prompt


def test_build_claude_prompt_uses_slash_command() -> None:
    config = RunConfig(command="autoresearch:plan", goal="Plan a loop")
    prompt = build_claude_prompt(config)
    assert "/autoresearch:plan" in prompt
    assert "Goal: Plan a loop" in prompt


def test_cursor_model_prefers_flags_then_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CURSOR_MODEL", "from-env")
    config = RunConfig(flags={"model": "from-flag"})
    assert cursor_model(config) == "from-flag"
    assert cursor_model(RunConfig()) == "from-env"


def test_run_cursor_agent_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CURSOR_API_KEY", raising=False)
    lines: list[tuple[str, str]] = []

    code, err = run_cursor_agent(
        RunConfig(project_path="."),
        on_line=lambda stream, line: lines.append((stream, line)),
        cancel_event=threading.Event(),
    )
    assert code == 1
    assert err is not None
    assert "CURSOR_API_KEY" in err


@patch("cursor_sdk.Agent")
def test_run_cursor_agent_success(mock_agent_cls: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CURSOR_API_KEY", "cursor_test_key")

    mock_agent = MagicMock()
    mock_agent.agent_id = "local-agent-1"
    mock_agent_cls.create.return_value.__enter__.return_value = mock_agent

    mock_run = MagicMock()
    mock_run.id = "run-1"
    mock_run.supports.return_value = True
    mock_run.messages.return_value = []
    mock_run.wait.return_value = MagicMock(status="finished")
    mock_agent.send.return_value = mock_run

    lines: list[str] = []
    started: list[tuple[str, str]] = []

    code, err = run_cursor_agent(
        RunConfig(project_path="."),
        on_line=lambda _stream, line: lines.append(line),
        cancel_event=threading.Event(),
        on_agent_started=lambda agent_id, run_id: started.append((agent_id, run_id)),
    )

    assert code == 0
    assert err is None
    assert started == [("local-agent-1", "run-1")]
    assert any("agent_id=local-agent-1" in line for line in lines)
    mock_agent.send.assert_called_once()
