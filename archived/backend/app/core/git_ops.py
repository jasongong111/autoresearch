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
    project_id: str = "."

    def to_dict(self) -> dict:
        return {
            "hash": self.hash,
            "shortHash": self.short_hash,
            "message": self.message,
            "date": self.date,
            "projectId": self.project_id,
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


def resolve_git_root(path: Path) -> Optional[Path]:
    """Return the git root for a directory, if any.

    Task projects often keep a nested repo (e.g. tasks/foo/.git) separate from the
    workspace root. Prefer the repo that contains ``path`` itself before walking up.
    """
    path = path.resolve()
    if (path / ".git").exists():
        return path
    output = _run_git(path, "rev-parse", "--show-toplevel")
    if output:
        return Path(output)
    return None


def list_experiment_commits(
    project_root: Path,
    limit: int = 20,
    *,
    project_id: str = ".",
) -> List[ExperimentCommit]:
    """Return recent commits matching experiment: prefix."""
    git_root = resolve_git_root(project_root)
    if git_root is None:
        return []

    output = _run_git(
        git_root,
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
                project_id=project_id,
            )
        )
    return commits


def commit_diff_stat(project_root: Path, commit_hash: str) -> Optional[str]:
    """Lightweight diff stat for a commit."""
    git_root = resolve_git_root(project_root)
    if git_root is None:
        return None
    return _run_git(git_root, "show", "--stat", "--oneline", commit_hash)
