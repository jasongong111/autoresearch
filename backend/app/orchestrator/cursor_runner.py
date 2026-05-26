"""Run autoresearch via the Cursor SDK (local agent)."""

from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from .models import RunConfig
from .prompt import build_cursor_prompt, cursor_model


OnLine = Callable[[str, str], None]
OnAgentStarted = Callable[[str, str], None]


def run_cursor_agent(
    config: RunConfig,
    on_line: OnLine,
    cancel_event: threading.Event,
    run_ref: Optional[Dict[str, Any]] = None,
    on_agent_started: Optional[OnAgentStarted] = None,
) -> Tuple[int, Optional[str]]:
    """Execute one autoresearch session with a local Cursor SDK agent.

    Returns (exit_code, error_message). Exit codes follow SDK conventions:
    0 = finished, 1 = startup failure, 2 = run error, 130 = cancelled.
    """
    try:
        from cursor_sdk import Agent, CursorAgentError, LocalAgentOptions
    except ImportError as exc:
        return 1, (
            "cursor-sdk is not installed. Run: pip install cursor-sdk "
            f"({exc})"
        )

    api_key = os.environ.get("CURSOR_API_KEY", "").strip()
    if not api_key:
        return 1, "CURSOR_API_KEY is required for the cursor runner"

    project_path = Path(config.project_path).resolve()
    if not project_path.is_dir():
        return 1, f"Project path does not exist: {config.project_path}"

    prompt = build_cursor_prompt(config)
    model = cursor_model(config)

    try:
        with Agent.create(
            model=model,
            api_key=api_key,
            local=LocalAgentOptions(
                cwd=str(project_path),
                setting_sources=["all"],
            ),
        ) as agent:
            if run_ref is not None:
                run_ref["agent"] = agent

            run = agent.send(prompt)
            if run_ref is not None:
                run_ref["run"] = run

            if on_agent_started is not None:
                on_agent_started(str(agent.agent_id), str(run.id))

            on_line("stdout", f"cursor agent_id={agent.agent_id} run_id={run.id} model={model}")

            for message in run.messages():
                if cancel_event.is_set():
                    if run.supports("cancel"):
                        run.cancel()
                    break
                if message.type == "assistant":
                    for block in message.message.content:
                        if block.type == "text" and block.text:
                            for line in block.text.splitlines():
                                on_line("stdout", line)

            result = run.wait()

            if cancel_event.is_set():
                return 130, "run cancelled"

            if result.status == "error":
                return 2, f"cursor run failed: {run.id}"

            return 0, None

    except CursorAgentError as exc:
        on_line("stderr", f"cursor startup failed: {exc.message}")
        return 1, exc.message
