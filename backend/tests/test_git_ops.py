"""Tests for per-project git discovery (nested task repos)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from backend.app.core.discovery import discover_projects, discover_runs
from backend.app.core.git_ops import list_experiment_commits, resolve_git_root
from backend.app.core.state import DashboardState


def test_resolve_git_root_uses_nested_task_dot_git(tmp_path: Path) -> None:
    task = tmp_path / "tasks" / "gemma3-math-skill-optimization"
    task.mkdir(parents=True)
    (task / ".git").mkdir()

    assert resolve_git_root(task) == task.resolve()


def test_list_experiment_commits_runs_git_in_task_repo(tmp_path: Path) -> None:
    task = tmp_path / "tasks" / "demo-task"
    task.mkdir(parents=True)
    (task / ".git").mkdir()

    with patch("backend.app.core.git_ops._run_git") as run_git:
        run_git.return_value = "full|short|experiment: improve skill|2025-01-01 00:00:00 +0000"
        commits = list_experiment_commits(task, project_id="tasks/demo-task")

    run_git.assert_called_once()
    assert run_git.call_args[0][0] == task.resolve()
    assert len(commits) == 1
    assert commits[0].message == "experiment: improve skill"
    assert commits[0].project_id == "tasks/demo-task"


def test_discover_projects_exposes_task_git_root(tmp_path: Path) -> None:
    task = tmp_path / "tasks" / "demo-task"
    task.mkdir(parents=True)
    (task / ".git").mkdir()

    projects = discover_projects(tmp_path, discover_runs(tmp_path))
    task_project = next(p for p in projects if p.project_id == "tasks/demo-task")
    assert task_project.git_root == str(task.resolve())
    assert task_project.is_task is True


def test_dashboard_git_scoped_to_task_project(tmp_path: Path) -> None:
    task = tmp_path / "tasks" / "demo-task"
    task.mkdir(parents=True)
    (task / ".git").mkdir()

    def fake_list(scan_root: Path, limit: int = 20, *, project_id: str = ".") -> list:
        if project_id == "tasks/demo-task":
            from backend.app.core.git_ops import ExperimentCommit

            return [
                ExperimentCommit(
                    hash="abc",
                    short_hash="abc",
                    message="experiment: task-only",
                    date="2025-01-01",
                    project_id=project_id,
                )
            ]
        if project_id == ".":
            from backend.app.core.git_ops import ExperimentCommit

            return [
                ExperimentCommit(
                    hash="def",
                    short_hash="def",
                    message="experiment: monorepo noise",
                    date="2025-01-02",
                    project_id=project_id,
                )
            ]
        return []

    state = DashboardState(tmp_path)
    with patch("backend.app.core.state.list_experiment_commits", side_effect=fake_list):
        state.refresh_git(force=True)

    task_commits = state.get_git_commits("tasks/demo-task")
    assert len(task_commits) == 1
    assert task_commits[0]["message"] == "experiment: task-only"

    all_commits = state.get_git_commits()
    messages = {c["message"] for c in all_commits}
    assert messages == {"experiment: task-only", "experiment: monorepo noise"}
