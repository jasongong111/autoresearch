"""Git experiment commit polling."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class ExperimentCommit:
    hash: str
    short_hash: str
    message: str
    date: str

    def to_dict(self) -> dict:
        return {
            "hash": self.hash,
            "shortHash": self.short_hash,
            "message": self.message,
            "date": self.date,
        }


def _run_git(project_root: Path, *args: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), *args],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def list_experiment_commits(project_root: Path, limit: int = 20) -> List[ExperimentCommit]:
    """Return recent commits matching experiment: prefix."""
    output = _run_git(
        project_root,
        "log",
        f"-{limit}",
        "--grep=experiment",
        "--format=%H|%h|%s|%ci",
    )
    if not output:
        return []

    commits: List[ExperimentCommit] = []
    for line in output.splitlines():
        parts = line.split("|", 3)
        if len(parts) < 4:
            continue
        commits.append(
            ExperimentCommit(
                hash=parts[0],
                short_hash=parts[1],
                message=parts[2],
                date=parts[3],
            )
        )
    return commits


def commit_diff_stat(project_root: Path, commit_hash: str) -> Optional[str]:
    """Lightweight diff stat for a commit."""
    return _run_git(project_root, "show", "--stat", "--oneline", commit_hash)
