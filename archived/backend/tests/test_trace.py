"""Tests for agent trace parsing."""

from pathlib import Path

from backend.app.core.trace import (
    discover_run_artifacts,
    gemma4_trace_file_path,
    parse_trace_analytics,
    parse_trace_jsonl,
)

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


def test_gemma4_trace_file_path_is_separate_from_observer_trace(tmp_path: Path):
    assert gemma4_trace_file_path(tmp_path) == tmp_path / ".autoresearch" / "gemma4-trace.jsonl"


def test_parse_trace_jsonl_preserves_structured_payloads():
    events = parse_trace_jsonl(FIXTURES / "gemma4_trace_structured.jsonl")

    assert len(events) == 2
    request = events[0].to_dict()
    response = events[1].to_dict()
    assert request["phase"] == "api_request"
    assert request["request"]["messages"][1]["content"] == "What is 40 + 2?"
    assert "Authorization" not in str(request["request"])
    assert response["phase"] == "api_response"
    assert response["response"]["choices"][0]["message"]["content"] == "42"


def test_parse_trace_analytics():
    analytics = parse_trace_analytics(FIXTURES / "analytics_trace.jsonl")

    assert analytics["traces"]["total"] == 3
    assert analytics["traces"]["byName"][0] == {"name": "research-loop", "count": 2}
    assert analytics["modelCosts"]["totalCostUsd"] == 0.15
    assert analytics["modelCosts"]["byModel"][0]["model"] == "claude-4.6"
    assert analytics["modelCosts"]["byModel"][0]["tokens"] == 3000
    assert analytics["modelCosts"]["byModel"][0]["costUsd"] == 0.12

    quality = analytics["scores"]["summary"][0]
    assert quality["name"] == "quality"
    assert quality["source"] == "API"
    assert quality["dataType"] == "NUMERIC"
    assert quality["count"] == 2
    assert quality["average"] == 0.5
    assert quality["zeros"] == 1
    assert quality["ones"] == 1

    assert analytics["timeSeries"]["traceObservationByLevel"][0]["traceCount"] == 2
    assert analytics["timeSeries"]["traceObservationByLevel"][0]["observationsByLevel"] == {
        "DEBUG": 1,
        "DEFAULT": 1,
    }
    assert analytics["userConsumption"]["costByUser"][0] == {
        "user": "bob",
        "totalCostUsd": 0.12,
    }
    assert analytics["userConsumption"]["traceCountByUser"][0] == {
        "user": "alice",
        "traceCount": 2,
    }

    assert analytics["latencies"]["trace"][0]["name"] == "research-loop"
    assert analytics["latencies"]["generation"][0]["name"] == "execute"
    assert analytics["modelLatencies"]["series"][0]["model"] == "claude-4.6"
    assert analytics["scoreAnalytics"]["quality|API|NUMERIC"]["histogram"][0] == {
        "bucket": "0",
        "count": 1,
    }


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
