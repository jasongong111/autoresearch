"""TSV parsing and normalization for all autoresearch log formats."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .schemas import (
    SCHEMA_BY_FILENAME,
    Command,
    NormalizedIteration,
    command_from_path,
    derive_outcome,
)

METRIC_DIRECTION_RE = re.compile(r"metric_direction:\s*(\S+)")


def _parse_float(value: str) -> Optional[float]:
    if not value or value.strip() in ("-", ""):
        return None
    cleaned = value.strip().replace("%", "").replace("+", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_int(value: str, default: int = 0) -> int:
    if not value or value.strip() in ("-", ""):
        return default
    try:
        return int(float(value.strip()))
    except ValueError:
        return default


def read_tsv_metadata(path: Path) -> Tuple[Optional[str], List[str]]:
    """Return (metric_direction, headers) from file header lines."""
    metric_direction: Optional[str] = None
    headers: List[str] = []
    if not path.exists():
        return metric_direction, headers
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                match = METRIC_DIRECTION_RE.search(stripped)
                if match:
                    metric_direction = match.group(1)
                continue
            headers = stripped.split("\t")
            break
    return metric_direction, headers


def parse_tsv_rows(path: Path) -> Tuple[Optional[str], List[str], List[Dict[str, str]]]:
    """Parse TSV file into list of row dicts keyed by header."""
    metric_direction, headers = read_tsv_metadata(path)
    if not headers:
        return metric_direction, [], []

    rows: List[Dict[str, str]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        header_found = False
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split("\t")
            if not header_found:
                header_found = True
                if parts != headers:
                    headers = parts
                continue
            row: Dict[str, str] = {}
            for i, key in enumerate(headers):
                row[key] = parts[i] if i < len(parts) else ""
            rows.append(row)
    return metric_direction, headers, rows


def _schema_for_file(path: Path, rel_path: str) -> Optional[Any]:
    name = path.name
    if name in SCHEMA_BY_FILENAME:
        return SCHEMA_BY_FILENAME[name]
    return None


def normalize_row(
    run_id: str,
    command: Command,
    row: Dict[str, str],
    row_index: int,
) -> NormalizedIteration:
    """Map a raw TSV row to NormalizedIteration."""
    cmd = command.value

    if command == Command.AUTORESEARCH:
        status = row.get("status", "")
        metric = _parse_float(row.get("metric", ""))
        return NormalizedIteration(
            run_id=run_id,
            command=cmd,
            index=_parse_int(row.get("iteration", ""), row_index),
            status=status,
            primary_value=metric,
            primary_label="metric",
            outcome=derive_outcome(status),
            description=row.get("description", ""),
            location="",
            commit=row.get("commit", "") if row.get("commit", "") != "-" else "",
            raw=dict(row),
        )

    if command == Command.SECURITY:
        status = row.get("confidence", row.get("severity", ""))
        return NormalizedIteration(
            run_id=run_id,
            command=cmd,
            index=_parse_int(row.get("iteration", ""), row_index),
            status=row.get("severity", ""),
            primary_value=1.0 if row.get("severity", "") not in ("-", "") else None,
            primary_label="finding",
            outcome=derive_outcome(row.get("confidence", "")),
            description=row.get("description", ""),
            location=row.get("location", ""),
            commit="",
            raw=dict(row),
        )

    if command == Command.DEBUG:
        result = row.get("result", "")
        return NormalizedIteration(
            run_id=run_id,
            command=cmd,
            index=_parse_int(row.get("iteration", ""), row_index),
            status=result,
            primary_value=None,
            primary_label="result",
            outcome=derive_outcome(result),
            description=row.get("description", row.get("hypothesis", "")),
            location=row.get("location", ""),
            commit="",
            raw=dict(row),
        )

    if command == Command.FIX:
        status = row.get("status", "")
        delta = _parse_float(row.get("delta", ""))
        return NormalizedIteration(
            run_id=run_id,
            command=cmd,
            index=_parse_int(row.get("iteration", ""), row_index),
            status=status,
            primary_value=delta,
            primary_label="delta",
            outcome=derive_outcome(status),
            description=row.get("description", ""),
            location=row.get("target", ""),
            commit="",
            raw=dict(row),
        )

    if command == Command.SCENARIO:
        classification = row.get("classification", "")
        return NormalizedIteration(
            run_id=run_id,
            command=cmd,
            index=_parse_int(row.get("iteration", ""), row_index),
            status=classification,
            primary_value=None,
            primary_label="classification",
            outcome=derive_outcome(classification),
            description=row.get("description", row.get("title", "")),
            location=row.get("parent", "") if row.get("parent", "") != "-" else "",
            commit="",
            raw=dict(row),
        )

    if command == Command.PREDICT:
        status = row.get("status", "")
        findings = _parse_float(row.get("findings_produced", ""))
        return NormalizedIteration(
            run_id=run_id,
            command=cmd,
            index=_parse_int(row.get("round", ""), row_index),
            status=status,
            primary_value=findings,
            primary_label="findings_produced",
            outcome=derive_outcome(status),
            description=row.get("persona", ""),
            location="",
            commit="",
            raw=dict(row),
        )

    if command == Command.LEARN:
        score = _parse_float(row.get("learn_score", "")) or _parse_float(row.get("validation_score", ""))
        return NormalizedIteration(
            run_id=run_id,
            command=cmd,
            index=_parse_int(row.get("iteration", ""), row_index),
            status=row.get("mode", ""),
            primary_value=score,
            primary_label="learn_score",
            outcome="success" if score and score >= 80 else "neutral",
            description=f"docs +{row.get('docs_generated', '0')} ~{row.get('docs_updated', '0')}",
            location="",
            commit="",
            raw=dict(row),
        )

    if command == Command.REASON:
        votes = _parse_float(row.get("votes", ""))
        return NormalizedIteration(
            run_id=run_id,
            command=cmd,
            index=_parse_int(row.get("round", ""), row_index),
            status=row.get("winner", ""),
            primary_value=votes,
            primary_label="votes",
            outcome="success",
            description=row.get("word_counts", ""),
            location="",
            commit="",
            raw=dict(row),
        )

    if command == Command.SHIP:
        return NormalizedIteration(
            run_id=run_id,
            command=cmd,
            index=row_index,
            status=row.get("shipped", ""),
            primary_value=_parse_float(row.get("checklist_score", "").split("/")[0] if "/" in row.get("checklist_score", "") else row.get("checklist_score", "")),
            primary_label="checklist_score",
            outcome="success" if row.get("shipped", "") == "pass" else "neutral",
            description=row.get("notes", ""),
            location=row.get("target", ""),
            commit="",
            raw=dict(row),
            logged_at=row.get("timestamp"),
        )

    if command in (Command.PROBE_CONSTRAINTS, Command.PROBE_QUESTIONS):
        return NormalizedIteration(
            run_id=run_id,
            command=cmd,
            index=_parse_int(row.get("round", ""), row_index),
            status=row.get("type", row.get("flag", "")),
            primary_value=_parse_float(row.get("atoms_extracted", "")),
            primary_label="atoms",
            outcome="neutral",
            description=row.get("atom", row.get("question", ""))[:200],
            location=row.get("persona", ""),
            commit="",
            raw=dict(row),
        )

    return NormalizedIteration(
        run_id=run_id,
        command=cmd,
        index=row_index,
        status="",
        primary_value=None,
        primary_label="",
        outcome="neutral",
        description="",
        location="",
        commit="",
        raw=dict(row),
    )


def parse_log_file(project_root: Path, rel_path: str) -> Tuple[Optional[str], List[str], List[NormalizedIteration]]:
    """Parse a log file and return metric_direction, headers, normalized iterations."""
    path = project_root / rel_path
    command = command_from_path(rel_path)
    metric_direction, headers, rows = parse_tsv_rows(path)
    iterations = [
        normalize_row(rel_path, command, row, i)
        for i, row in enumerate(rows)
    ]
    return metric_direction, headers, iterations


def compute_summary(iterations: List[NormalizedIteration], metric_direction: Optional[str]) -> Dict[str, Any]:
    """Aggregate iteration stats for dashboard summary cards."""
    if not iterations:
        return {
            "total": 0,
            "outcomes": {},
            "bestPrimaryValue": None,
            "consecutiveDiscards": 0,
            "stuckWarning": False,
            "statusCounts": {},
        }

    outcomes: Dict[str, int] = {}
    status_counts: Dict[str, int] = {}
    values: List[float] = []
    discard_streak = 0
    max_discard_streak = 0

    for it in iterations:
        outcomes[it.outcome] = outcomes.get(it.outcome, 0) + 1
        status_counts[it.status] = status_counts.get(it.status, 0) + 1
        if it.primary_value is not None:
            values.append(it.primary_value)
        st = it.status.lower()
        if st in ("discard", "fail", "disproven"):
            discard_streak += 1
            max_discard_streak = max(max_discard_streak, discard_streak)
        else:
            discard_streak = 0

    higher_is_better = metric_direction != "lower_is_better"
    best: Optional[float] = None
    if values:
        best = max(values) if higher_is_better else min(values)

    return {
        "total": len(iterations),
        "outcomes": outcomes,
        "bestPrimaryValue": best,
        "consecutiveDiscards": max_discard_streak,
        "stuckWarning": max_discard_streak >= 5,
        "statusCounts": status_counts,
        "metricDirection": metric_direction,
    }
