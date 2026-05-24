"""Canonical TSV schemas and normalized iteration models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class Command(str, Enum):
    AUTORESEARCH = "autoresearch"
    SECURITY = "security"
    DEBUG = "debug"
    FIX = "fix"
    SCENARIO = "scenario"
    PREDICT = "predict"
    LEARN = "learn"
    REASON = "reason"
    SHIP = "ship"
    PROBE_CONSTRAINTS = "probe_constraints"
    PROBE_QUESTIONS = "probe_questions"


@dataclass(frozen=True)
class LogSchema:
    command: Command
    filename: str
    glob_pattern: str
    headers: tuple[str, ...]
    index_column: str = "iteration"


LOG_SCHEMAS: List[LogSchema] = [
    LogSchema(
        Command.AUTORESEARCH,
        "autoresearch-results.tsv",
        "autoresearch-results.tsv",
        (
            "iteration",
            "commit",
            "metric",
            "delta",
            "guard",
            "guard-metric",
            "status",
            "description",
        ),
    ),
    LogSchema(
        Command.SECURITY,
        "security-audit-results.tsv",
        "security/*/security-audit-results.tsv",
        (
            "iteration",
            "vector",
            "severity",
            "owasp",
            "stride",
            "confidence",
            "location",
            "description",
        ),
    ),
    LogSchema(
        Command.DEBUG,
        "debug-results.tsv",
        "debug/*/debug-results.tsv",
        (
            "iteration",
            "type",
            "hypothesis",
            "result",
            "severity",
            "location",
            "description",
        ),
    ),
    LogSchema(
        Command.FIX,
        "fix-results.tsv",
        "fix/*/fix-results.tsv",
        (
            "iteration",
            "category",
            "target",
            "delta",
            "guard",
            "status",
            "description",
        ),
    ),
    LogSchema(
        Command.SCENARIO,
        "scenario-results.tsv",
        "scenario/*/scenario-results.tsv",
        (
            "iteration",
            "dimension",
            "classification",
            "severity",
            "title",
            "description",
            "parent",
        ),
    ),
    LogSchema(
        Command.PREDICT,
        "predict-results.tsv",
        "predict/*/predict-results.tsv",
        ("round", "persona", "findings_produced", "findings_revised", "challenges_issued", "flip_count", "status"),
        index_column="round",
    ),
    LogSchema(
        Command.LEARN,
        "learn-results.tsv",
        "learn/*/learn-results.tsv",
        (
            "iteration",
            "mode",
            "docs_generated",
            "docs_updated",
            "validation_score",
            "fix_iterations",
            "learn_score",
            "duration_s",
        ),
    ),
    LogSchema(
        Command.REASON,
        "reason-results.tsv",
        "reason/*/reason-results.tsv",
        ("round", "winner", "votes", "consecutive_wins", "word_counts"),
        index_column="round",
    ),
    LogSchema(
        Command.SHIP,
        "ship-log.tsv",
        "ship/*/ship-log.tsv",
        ("timestamp", "type", "target", "checklist_score", "dry_run", "shipped", "verified", "duration", "notes"),
        index_column="timestamp",
    ),
    LogSchema(
        Command.PROBE_CONSTRAINTS,
        "constraints.tsv",
        "probe/*/constraints.tsv",
        ("round", "persona", "atom", "type", "flag", "source"),
        index_column="round",
    ),
    LogSchema(
        Command.PROBE_QUESTIONS,
        "questions-asked.tsv",
        "probe/*/questions-asked.tsv",
        ("round", "persona", "question", "answer", "atoms_extracted"),
        index_column="round",
    ),
]

SCHEMA_BY_FILENAME: Dict[str, LogSchema] = {s.filename: s for s in LOG_SCHEMAS}


def command_from_path(rel_path: str) -> Command:
    name = rel_path.split("/")[-1]
    if name in SCHEMA_BY_FILENAME:
        return SCHEMA_BY_FILENAME[name].command
    if "probe" in rel_path and "constraints" in name:
        return Command.PROBE_CONSTRAINTS
    if "probe" in rel_path and "questions" in name:
        return Command.PROBE_QUESTIONS
    return Command.AUTORESEARCH


SUCCESS_STATUSES = frozenset(
    {
        "keep",
        "keep (reworked)",
        "fixed",
        "baseline",
        "confirmed",
        "new",
        "variant",
        "pass",
        "independent_analysis",
    }
)

FAILURE_STATUSES = frozenset(
    {
        "discard",
        "crash",
        "fail",
        "hook-blocked",
        "metric-error",
        "blocked",
        "disproven",
    }
)


def derive_outcome(status: str) -> str:
    s = (status or "").lower().strip()
    if s in SUCCESS_STATUSES or s.startswith("keep"):
        return "success"
    if s in FAILURE_STATUSES:
        return "failure"
    if s in ("no-op", "rework"):
        return "neutral"
    return "neutral"


@dataclass
class NormalizedIteration:
    run_id: str
    command: str
    index: int
    status: str
    primary_value: Optional[float]
    primary_label: str
    outcome: str
    description: str
    location: str
    commit: str
    raw: Dict[str, Any] = field(default_factory=dict)
    logged_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "runId": self.run_id,
            "command": self.command,
            "index": self.index,
            "status": self.status,
            "primaryValue": self.primary_value,
            "primaryLabel": self.primary_label,
            "outcome": self.outcome,
            "description": self.description,
            "location": self.location,
            "commit": self.commit,
            "raw": self.raw,
            "loggedAt": self.logged_at,
        }


@dataclass
class ProjectInfo:
    project_id: str
    project_path: str
    name: str
    run_count: int = 0
    is_task: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "projectId": self.project_id,
            "projectPath": self.project_path,
            "name": self.name,
            "runCount": self.run_count,
            "isTask": self.is_task,
        }


@dataclass
class RunInfo:
    run_id: str
    command: str
    path: str
    last_modified: float
    row_count: int
    metric_direction: Optional[str] = None
    headers: List[str] = field(default_factory=list)
    project_id: str = "."
    project_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "runId": self.run_id,
            "command": self.command,
            "path": self.path,
            "lastModified": self.last_modified,
            "rowCount": self.row_count,
            "metricDirection": self.metric_direction,
            "headers": self.headers,
            "projectId": self.project_id,
            "projectPath": self.project_path,
        }
