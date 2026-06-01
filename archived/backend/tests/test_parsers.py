"""Unit tests for TSV parsers."""

from pathlib import Path

import pytest

from backend.app.core.parsers import compute_summary, parse_log_file, parse_tsv_rows
from backend.app.core.schemas import Command, command_from_path

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_autoresearch():
    path = FIXTURES / "autoresearch-results.tsv"
    metric_dir, headers, rows = parse_tsv_rows(path)
    assert metric_dir == "higher_is_better"
    assert "iteration" in headers
    assert len(rows) == 3

    md, hdrs, iterations = parse_log_file(FIXTURES.parent, "fixtures/autoresearch-results.tsv")
    assert len(iterations) == 3
    assert iterations[1].status == "keep"
    assert iterations[1].primary_value == 74.5
    assert iterations[1].outcome == "success"


def test_parse_fix():
    md, hdrs, iterations = parse_log_file(FIXTURES.parent, "fixtures/fix-results.tsv")
    assert iterations[1].command == "fix"
    assert iterations[1].primary_value == -2.0
    assert iterations[2].outcome == "failure"


def test_parse_security():
    md, hdrs, iterations = parse_log_file(FIXTURES.parent, "fixtures/security-audit-results.tsv")
    assert iterations[1].location == "src/api/users.ts:42"


def test_parse_predict():
    md, hdrs, iterations = parse_log_file(FIXTURES.parent, "fixtures/predict-results.tsv")
    assert iterations[0].index == 0
    assert iterations[0].primary_label == "findings_produced"


def test_compute_summary_stuck():
    md, _, iterations = parse_log_file(FIXTURES.parent, "fixtures/autoresearch-results.tsv")
    summary = compute_summary(iterations, "higher_is_better")
    assert summary["total"] == 3
    assert "outcomes" in summary


def test_command_from_path():
    assert command_from_path("fix/foo/fix-results.tsv") == Command.FIX
    assert command_from_path("autoresearch-results.tsv") == Command.AUTORESEARCH
