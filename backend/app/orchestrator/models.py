"""Pydantic models for run orchestration."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class RunConfig(BaseModel):
    """A reusable autoresearch run configuration."""

    id: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y%m%d-%H%M%S-%f")[:-3])
    name: str = "Untitled run"
    command: str = "autoresearch"  # autoresearch, autoresearch:plan, autoresearch:debug, etc.
    goal: str = ""
    scope: str = ""
    metric: str = ""
    verify: str = ""
    guard: Optional[str] = None
    direction: Optional[str] = "higher"
    iterations: Optional[int] = None
    flags: dict[str, Any] = Field(default_factory=dict)
    runner: str = "claude"  # claude | codex | opencode
    project_path: str = "."
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RunInstance(BaseModel):
    """A single execution of a RunConfig."""

    id: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y%m%d-%H%M%S-%f")[:-3])
    config_id: str
    status: Literal["queued", "running", "completed", "failed", "stopped"] = "queued"
    pid: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    stdout_tail: list[str] = Field(default_factory=list)
    stderr_tail: list[str] = Field(default_factory=list)
