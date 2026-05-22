"""Tests for run discovery."""

from pathlib import Path

from dashboard.server.discovery import active_run_id, discover_runs

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
