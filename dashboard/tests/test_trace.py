"""Tests for agent trace parsing."""

from pathlib import Path

from dashboard.server.trace import discover_run_artifacts, parse_trace_jsonl

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_trace_jsonl():
    events = parse_trace_jsonl(FIXTURES / "trace.jsonl")
    assert len(events) == 9
    assert events[0].phase == "setup"
    assert events[0].iteration == 0
    assert events[4].level == "success"
    assert events[4].phase == "decide"
    assert events[8].level == "failure"


def test_parse_trace_jsonl_missing():
    assert parse_trace_jsonl(Path("/nonexistent/trace.jsonl")) == []


def test_discover_run_artifacts(tmp_path: Path):
    run_dir = tmp_path / "reason" / "260521-1400-demo"
    run_dir.mkdir(parents=True)
    tsv = run_dir / "reason-results.tsv"
    tsv.write_text("round\twinner\tvotes\n1\tA\t3\n")
    (run_dir / "judge-transcripts.md").write_text("# Round 1\nJudge A preferred clarity.")
    (run_dir / "lineage.md").write_text("# Lineage\nRound 1: A wins.")

    artifacts = discover_run_artifacts(tmp_path, "reason/260521-1400-demo/reason-results.tsv")
    names = {a.name for a in artifacts}
    assert "judge-transcripts.md" in names
    assert "lineage.md" in names
    assert all(a.content for a in artifacts)
