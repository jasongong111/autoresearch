"""API smoke tests."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from dashboard.server.app import create_app
from dashboard.server.state import DashboardState

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
