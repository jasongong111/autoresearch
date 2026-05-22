"""Discover autoresearch log files in a target project."""

from __future__ import annotations

from pathlib import Path
from typing import List

from .parsers import parse_tsv_rows, read_tsv_metadata
from .schemas import LOG_SCHEMAS, RunInfo, command_from_path


def discover_runs(project_root: Path) -> List[RunInfo]:
    """Glob-scan project for all known autoresearch log files."""
    project_root = project_root.resolve()
    runs: List[RunInfo] = []

    for schema in LOG_SCHEMAS:
        pattern = schema.glob_pattern
        for path in sorted(project_root.glob(pattern)):
            if not path.is_file():
                continue
            try:
                rel = path.relative_to(project_root).as_posix()
            except ValueError:
                continue
            metric_direction, headers = read_tsv_metadata(path)
            _, _, rows = parse_tsv_rows(path)
            stat = path.stat()
            runs.append(
                RunInfo(
                    run_id=rel,
                    command=command_from_path(rel).value,
                    path=str(path),
                    last_modified=stat.st_mtime,
                    row_count=len(rows),
                    metric_direction=metric_direction,
                    headers=list(headers),
                )
            )

    runs.sort(key=lambda r: r.last_modified, reverse=True)
    return runs


def active_run_id(runs: List[RunInfo]) -> str | None:
    if not runs:
        return None
    return runs[0].run_id
