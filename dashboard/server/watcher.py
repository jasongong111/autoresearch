"""Filesystem watcher for TSV log updates."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Optional

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from .state import DashboardState
from .trace import RUN_TRACE_ARTIFACTS


class LogFileHandler(FileSystemEventHandler):
    def __init__(self, state: DashboardState, project_root: Path) -> None:
        self.state = state
        self.project_root = project_root.resolve()

    def _rel_path(self, path: str) -> str | None:
        try:
            return Path(path).resolve().relative_to(self.project_root).as_posix()
        except ValueError:
            return None

    def _maybe_notify(self, path: str) -> None:
        rel = self._rel_path(path)
        if not rel:
            return
        if rel.endswith(".tsv") or rel.endswith("session.json") or rel.endswith("trace.jsonl"):
            if rel.endswith("session.json"):
                self.state.refresh_runs()
                return
            if rel.endswith("trace.jsonl"):
                self.state.on_trace_changed()
                return
            self.state.on_file_changed(rel)
            return
        if rel.endswith("conversation.jsonl"):
            self.state.on_conversation_changed()
            return
        if Path(rel).name in RUN_TRACE_ARTIFACTS:
            run_dir = str(Path(rel).parent)
            self.state.refresh_runs()
            for run in self.state.runs:
                if str(Path(run.run_id).parent) == run_dir:
                    self.state.on_artifacts_changed(run.run_id)

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._maybe_notify(event.src_path)

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._maybe_notify(event.src_path)


def start_watcher(state: DashboardState) -> Observer:
    handler = LogFileHandler(state, state.project_root)
    observer = Observer()
    observer.schedule(handler, str(state.project_root), recursive=True)
    observer.start()
    return observer


def start_transcript_watcher(state: DashboardState) -> Optional[Observer]:
    """Watch Cursor agent-transcript directories (outside project root)."""
    if not state.transcript_dirs:
        return None

    class TranscriptHandler(FileSystemEventHandler):
        def _notify(self, path: str) -> None:
            if path.endswith(".jsonl"):
                state.on_conversation_changed()

        def on_modified(self, event: FileSystemEvent) -> None:
            if not event.is_directory:
                self._notify(event.src_path)

        def on_created(self, event: FileSystemEvent) -> None:
            if not event.is_directory:
                self._notify(event.src_path)

    transcript_handler = TranscriptHandler()
    observer = Observer()
    for tdir in state.transcript_dirs:
        if tdir.is_dir():
            observer.schedule(transcript_handler, str(tdir), recursive=True)
    observer.start()
    return observer


def start_periodic_rescan(state: DashboardState, interval: float = 30.0) -> threading.Thread:
    def loop() -> None:
        while True:
            time.sleep(interval)
            state.refresh_runs()
            state.on_conversation_changed()
            if state.refresh_git():
                state.on_git_changed()

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    return thread
