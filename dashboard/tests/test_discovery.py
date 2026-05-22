"""Tests for run discovery."""

from pathlib import Path

from dashboard.server.discovery import active_run_id, discover_projects, discover_runs

FIXTURES = Path(__file__).parent / "fixtures"


def test_discover_runs_in_fixtures_dir(tmp_path: Path):
    # Copy fixture as root-level autoresearch log
    src = FIXTURES / "autoresearch-results.tsv"
    dest = tmp_path / "autoresearch-results.tsv"
    dest.write_text(src.read_text())
    runs = discover_runs(tmp_path)
    assert len(runs) == 1
    assert runs[0].command == "autoresearch"
    assert runs[0].row_count == 3
    assert active_run_id(runs) == "autoresearch-results.tsv"


def test_discover_nested_fix(tmp_path: Path):
    fix_dir = tmp_path / "fix" / "260521-auth"
    fix_dir.mkdir(parents=True)
    (fix_dir / "fix-results.tsv").write_text(
        (FIXTURES / "fix-results.tsv").read_text()
    )
    runs = discover_runs(tmp_path)
    assert any(r.command == "fix" for r in runs)


def test_discover_runs_in_tasks_projects(tmp_path: Path):
    task_project = tmp_path / "tasks" / "agentic-skill-demo"
    task_project.mkdir(parents=True)
    (task_project / "autoresearch-results.tsv").write_text(
        (FIXTURES / "autoresearch-results.tsv").read_text()
    )
    fix_dir = task_project / "fix" / "260521-auth"
    fix_dir.mkdir(parents=True)
    (fix_dir / "fix-results.tsv").write_text((FIXTURES / "fix-results.tsv").read_text())

    runs = discover_runs(tmp_path)
    run_ids = {r.run_id for r in runs}

    assert "tasks/agentic-skill-demo/autoresearch-results.tsv" in run_ids
    assert "tasks/agentic-skill-demo/fix/260521-auth/fix-results.tsv" in run_ids
    assert {r.project_id for r in runs} == {"tasks/agentic-skill-demo"}


def test_discover_projects_includes_tasks_without_runs(tmp_path: Path):
    task_with_runs = tmp_path / "tasks" / "agentic-skill-demo"
    task_with_runs.mkdir(parents=True)
    (task_with_runs / "autoresearch-results.tsv").write_text(
        (FIXTURES / "autoresearch-results.tsv").read_text()
    )
    task_empty = tmp_path / "tasks" / "gemma4-skill-optimization"
    task_empty.mkdir(parents=True)

    runs = discover_runs(tmp_path)
    projects = discover_projects(tmp_path, runs)
    project_ids = {p.project_id for p in projects}

    assert project_ids == {".", "tasks/agentic-skill-demo", "tasks/gemma4-skill-optimization"}
    empty = next(p for p in projects if p.project_id == "tasks/gemma4-skill-optimization")
    assert empty.run_count == 0
    assert empty.is_task is True
    active = next(p for p in projects if p.project_id == "tasks/agentic-skill-demo")
    assert active.run_count == 1
