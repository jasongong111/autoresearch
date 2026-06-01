"""Shared paths for the skill agent package."""

from __future__ import annotations

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent
WEB_DIR = PACKAGE_DIR / "web"
SESSION_DB = REPO_ROOT / "logs" / "agent-core" / "agent_core_sessions.db"
TRACE_LOG = REPO_ROOT / "logs" / "agent-core" / "agent_core_trace.jsonl"


def default_skill_roots() -> tuple[Path, ...]:
    return (
        REPO_ROOT / ".agents" / "skills",
        REPO_ROOT / ".claude" / "skills",
    )
