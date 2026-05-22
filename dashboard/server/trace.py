"""Agent trace parsing — live JSONL events and run-directory artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

TRACE_PATH = ".autoresearch/trace.jsonl"

# Markdown / JSONL artifacts that carry agent reasoning traces per command folder.
RUN_TRACE_ARTIFACTS: Dict[str, str] = {
    "persona-debates.md": "Persona debates",
    "judge-transcripts.md": "Judge transcripts",
    "lineage.md": "Lineage",
    "reason-lineage.jsonl": "Lineage (JSONL)",
    "findings.md": "Findings",
    "eliminated.md": "Eliminated hypotheses",
    "contradictions.md": "Contradictions",
    "hidden-assumptions.md": "Hidden assumptions",
    "overview.md": "Overview",
    "hypothesis-queue.md": "Hypothesis queue",
    "scout-context.md": "Scout context",
    "summary.md": "Summary",
}


@dataclass
class TraceEvent:
    ts: str
    phase: str
    message: str
    iteration: Optional[int] = None
    round: Optional[int] = None
    detail: Optional[str] = None
    level: str = "info"

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "ts": self.ts,
            "phase": self.phase,
            "message": self.message,
            "level": self.level,
        }
        if self.iteration is not None:
            out["iteration"] = self.iteration
        if self.round is not None:
            out["round"] = self.round
        if self.detail:
            out["detail"] = self.detail
        return out


@dataclass
class TraceArtifact:
    name: str
    title: str
    content: str
    last_modified: float
    kind: str = "markdown"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "title": self.title,
            "content": self.content,
            "lastModified": self.last_modified,
            "kind": self.kind,
        }


def trace_file_path(project_root: Path) -> Path:
    return project_root / TRACE_PATH


def parse_trace_jsonl(path: Path) -> List[TraceEvent]:
    if not path.is_file():
        return []
    events: List[TraceEvent] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict):
            continue
        message = str(obj.get("message") or obj.get("msg") or "").strip()
        phase = str(obj.get("phase") or "info").strip()
        if not message:
            continue
        iteration = _optional_int(obj.get("iteration"))
        round_num = _optional_int(obj.get("round"))
        events.append(
            TraceEvent(
                ts=str(obj.get("ts") or obj.get("timestamp") or ""),
                phase=phase,
                message=message,
                iteration=iteration,
                round=round_num,
                detail=_optional_str(obj.get("detail")),
                level=str(obj.get("level") or "info").lower(),
            )
        )
    return events


def discover_run_artifacts(project_root: Path, run_id: str) -> List[TraceArtifact]:
    """Find trace markdown/jsonl files in the same directory as a run TSV."""
    run_path = (project_root / run_id).resolve()
    if not run_path.is_file():
        return []
    run_dir = run_path.parent
    artifacts: List[TraceArtifact] = []
    for filename, title in RUN_TRACE_ARTIFACTS.items():
        path = run_dir / filename
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        kind = "jsonl" if filename.endswith(".jsonl") else "markdown"
        artifacts.append(
            TraceArtifact(
                name=filename,
                title=title,
                content=content,
                last_modified=path.stat().st_mtime,
                kind=kind,
            )
        )
    artifacts.sort(key=lambda a: a.name)
    return artifacts


def _optional_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    return s or None
