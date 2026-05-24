"""API smoke tests."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.core.app import create_app
from backend.app.core.state import DashboardState

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def client(tmp_path: Path):
    (tmp_path / "autoresearch-results.tsv").write_text(
        (FIXTURES / "autoresearch-results.tsv").read_text()
    )
    state = DashboardState(tmp_path)
    state.refresh_runs()
    app = create_app(state, static_dir=None)
    return TestClient(app)


def test_health(client: TestClient):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_runs_and_iterations(client: TestClient):
    runs = client.get("/api/runs").json()
    assert len(runs["runs"]) >= 1
    run_id = runs["runs"][0]["runId"]
    iters = client.get(f"/api/runs/{run_id}/iterations").json()
    assert len(iters["iterations"]) == 3
    summary = client.get(f"/api/runs/{run_id}/summary").json()
    assert summary["total"] == 3


def test_trace_and_artifacts(client: TestClient, tmp_path: Path):
    trace_dir = tmp_path / ".autoresearch"
    trace_dir.mkdir()
    (trace_dir / "trace.jsonl").write_text(
        (Path(__file__).parent / "fixtures" / "trace.jsonl").read_text()
    )
    state = client.app.state.dashboard  # type: ignore[attr-defined]
    state.refresh_runs()
    trace = client.get("/api/trace").json()
    assert len(trace["events"]) == 9
    assert trace["events"][0]["phase"] == "setup"

    runs = client.get("/api/runs").json()
    run_id = runs["runs"][0]["runId"]
    artifacts = client.get(f"/api/runs/{run_id}/artifacts").json()
    assert "artifacts" in artifacts


def test_projects_api(client: TestClient, tmp_path: Path):
    task_with_runs = tmp_path / "tasks" / "agentic-skill-demo"
    task_with_runs.mkdir(parents=True)
    (task_with_runs / "autoresearch-results.tsv").write_text(
        (FIXTURES / "autoresearch-results.tsv").read_text()
    )
    (tmp_path / "tasks" / "gemma4-skill-optimization").mkdir(parents=True)
    state = client.app.state.dashboard  # type: ignore[attr-defined]
    state.refresh_runs()

    projects = client.get("/api/projects").json()["projects"]
    project_ids = {p["projectId"] for p in projects}
    assert project_ids == {".", "tasks/agentic-skill-demo", "tasks/gemma4-skill-optimization"}

    runs = client.get("/api/runs").json()
    assert "projects" in runs
    assert len(runs["projects"]) == 3


def test_task_project_trace_api(client: TestClient, tmp_path: Path):
    task_project = tmp_path / "tasks" / "agentic-skill-demo"
    task_project.mkdir(parents=True)
    (task_project / "autoresearch-results.tsv").write_text(
        (FIXTURES / "autoresearch-results.tsv").read_text()
    )
    trace_dir = task_project / ".autoresearch"
    trace_dir.mkdir()
    (trace_dir / "trace.jsonl").write_text((FIXTURES / "analytics_trace.jsonl").read_text())
    state = client.app.state.dashboard  # type: ignore[attr-defined]
    state.refresh_runs()

    run_id = "tasks/agentic-skill-demo/autoresearch-results.tsv"
    run = client.get(f"/api/runs/{run_id}").json()
    assert run["projectId"] == "tasks/agentic-skill-demo"
    assert run["projectPath"].endswith("tasks/agentic-skill-demo")

    trace = client.get(f"/api/runs/{run_id}/trace").json()
    assert trace["events"] == []
    analytics = client.get(f"/api/runs/{run_id}/analytics").json()
    assert analytics["traces"]["total"] == 3


def test_task_project_gemma4_trace_api(client: TestClient, tmp_path: Path):
    task_project = tmp_path / "tasks" / "gemma4-skill-optimization"
    task_project.mkdir(parents=True)
    (task_project / "autoresearch-results.tsv").write_text(
        (FIXTURES / "autoresearch-results.tsv").read_text()
    )
    trace_dir = task_project / ".autoresearch"
    trace_dir.mkdir()
    (trace_dir / "trace.jsonl").write_text((FIXTURES / "trace.jsonl").read_text())
    (trace_dir / "gemma4-trace.jsonl").write_text((FIXTURES / "gemma4_trace.jsonl").read_text())
    state = client.app.state.dashboard  # type: ignore[attr-defined]
    state.refresh_runs()

    run_id = "tasks/gemma4-skill-optimization/autoresearch-results.tsv"
    gemma4_trace = client.get(f"/api/runs/{run_id}/gemma4-trace").json()

    assert len(gemma4_trace["events"]) == 3
    assert gemma4_trace["events"][0]["phase"] == "prompt"
    assert gemma4_trace["events"][2]["level"] == "success"


def test_task_project_gemma3_trace_api_preserves_payloads(client: TestClient, tmp_path: Path):
    task_project = tmp_path / "tasks" / "gemma3-skill-optimization"
    task_project.mkdir(parents=True)
    (task_project / "autoresearch-results.tsv").write_text(
        (FIXTURES / "autoresearch-results.tsv").read_text()
    )
    trace_dir = task_project / ".autoresearch"
    trace_dir.mkdir()
    (trace_dir / "gemma3-trace.jsonl").write_text((FIXTURES / "gemma3_trace.jsonl").read_text())
    state = client.app.state.dashboard  # type: ignore[attr-defined]
    state.refresh_runs()

    run_id = "tasks/gemma3-skill-optimization/autoresearch-results.tsv"
    gemma3_trace = client.get(f"/api/runs/{run_id}/gemma3-trace").json()

    assert len(gemma3_trace["events"]) == 2
    assert gemma3_trace["events"][0]["phase"] == "api_request"
    assert gemma3_trace["events"][0]["request"]["messages"][1]["content"] == "What is 40 + 2?"
    assert gemma3_trace["events"][1]["response"]["choices"][0]["message"]["content"] == "42"


def test_analytics_api(client: TestClient, tmp_path: Path):
    trace_dir = tmp_path / ".autoresearch"
    trace_dir.mkdir()
    (trace_dir / "trace.jsonl").write_text((FIXTURES / "analytics_trace.jsonl").read_text())
    state = client.app.state.dashboard  # type: ignore[attr-defined]
    state.refresh_runs()

    analytics = client.get("/api/analytics").json()
    assert analytics["traces"]["total"] == 3
    assert analytics["modelCosts"]["totalCostUsd"] == 0.15
    assert analytics["scores"]["total"] == 4
    assert analytics["latencies"]["observation"][0]["p99Ms"] == 1500


def test_conversations_api(client: TestClient, tmp_path: Path):
    conv_dir = tmp_path / ".autoresearch"
    conv_dir.mkdir()
    (conv_dir / "conversation.jsonl").write_text(
        (FIXTURES / "conversation.jsonl").read_text()
    )
    state = client.app.state.dashboard  # type: ignore[attr-defined]
    state.refresh_runs()
    listing = client.get("/api/conversations").json()
    assert len(listing["conversations"]) >= 1
    conv_id = listing["conversations"][0]["id"]
    detail = client.get(f"/api/conversations/{conv_id}/turns").json()
    assert len(detail["turns"]) >= 2
    assert detail["turns"][0]["role"] == "user"
