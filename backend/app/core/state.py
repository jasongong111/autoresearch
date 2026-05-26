"""Shared application state for watcher + API."""

from __future__ import annotations

import asyncio
import json
import threading
import time
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional, Set

from backend.app.core.discovery import active_run_id, discover_project_roots, discover_projects, discover_runs
from backend.app.core.git_ops import (
    ExperimentCommit,
    commit_diff_stat,
    list_experiment_commits,
    resolve_git_root,
)
from backend.app.core.parsers import compute_summary, parse_log_file
from backend.app.core.schemas import ProjectInfo, RunInfo
from backend.app.core.conversations import (
    conversation_sources_fingerprint,
    discover_conversations,
    get_conversation_turns,
    resolve_transcript_dirs,
)
from backend.app.core.trace import (
    discover_run_artifacts,
    gemma3_trace_file_path,
    gemma4_trace_file_path,
    parse_trace_analytics,
    parse_trace_jsonl,
    trace_file_path,
)


class DashboardState:
    def __init__(self, project_root: Path, transcript_dirs: Optional[List[Path]] = None) -> None:
        self.project_root = project_root.resolve()
        self.transcript_dirs = resolve_transcript_dirs(self.project_root, transcript_dirs)
        self.runs: List[RunInfo] = []
        self.projects: List[ProjectInfo] = []
        self.iterations_cache: Dict[str, List[dict]] = {}
        self.summary_cache: Dict[str, dict] = {}
        self.git_commits: List[ExperimentCommit] = []
        self._git_commits_by_project: Dict[str, List[ExperimentCommit]] = {}
        self._git_roots_by_project: Dict[str, Path] = {}
        self.active_run_id: Optional[str] = None
        self._lock = threading.Lock()
        self._subscribers: Set[asyncio.Queue] = set()
        self._last_git_poll = 0.0
        self._session: Optional[dict] = None
        self._trace_events: List[dict] = []
        self._trace_analytics: dict = {}
        self._trace_mtime: float = 0.0
        self._artifacts_cache: Dict[str, List[dict]] = {}
        self._conversations: List[dict] = []
        self._conversation_turns_cache: Dict[str, List[dict]] = {}
        self._conversations_fingerprint: str = ""
        self._experiments: List[dict] = []
        self._experiments_mtime: float = 0.0
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def refresh_runs(self) -> None:
        with self._lock:
            self.runs = discover_runs(self.project_root)
            self.projects = discover_projects(self.project_root, self.runs)
            self.active_run_id = active_run_id(self.runs)
            self._load_session()
            self._load_trace(force=True)
            self._load_experiments(force=True)
            self._load_conversations(force=True)

    def _load_session(self) -> None:
        self._session = self._read_session(self.project_root)

    def _read_session(self, project_root: Path) -> Optional[dict]:
        session_path = project_root / ".autoresearch" / "session.json"
        if session_path.exists():
            try:
                return json.loads(session_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return None
        return None

    def get_session(self) -> Optional[dict]:
        return self._session

    def _project_root_for_run(self, run_id: str) -> Path:
        run = self.get_run(run_id)
        if run and run.project_path:
            return Path(run.project_path)
        return self.project_root

    def get_run_session(self, run_id: str) -> Optional[dict]:
        return self._read_session(self._project_root_for_run(run_id))

    def _load_trace(self, force: bool = False) -> bool:
        path = trace_file_path(self.project_root)
        if not path.is_file():
            if self._trace_events:
                self._trace_events = []
                self._trace_analytics = {}
                self._trace_mtime = 0.0
                return True
            return False
        mtime = path.stat().st_mtime
        if not force and mtime == self._trace_mtime:
            return False
        events = parse_trace_jsonl(path)
        self._trace_events = [e.to_dict() for e in events]
        self._trace_analytics = parse_trace_analytics(path)
        self._trace_mtime = mtime
        return True

    def get_trace(self) -> List[dict]:
        with self._lock:
            self._load_trace()
            return list(self._trace_events)

    def get_analytics(self) -> dict:
        with self._lock:
            self._load_trace()
            return dict(self._trace_analytics)

    def get_run_trace(self, run_id: str) -> List[dict]:
        path = trace_file_path(self._project_root_for_run(run_id))
        return [event.to_dict() for event in parse_trace_jsonl(path)]

    def get_run_gemma3_trace(self, run_id: str) -> List[dict]:
        path = gemma3_trace_file_path(self._project_root_for_run(run_id))
        return [event.to_dict() for event in parse_trace_jsonl(path)]

    def get_run_gemma4_trace(self, run_id: str) -> List[dict]:
        path = gemma4_trace_file_path(self._project_root_for_run(run_id))
        return [event.to_dict() for event in parse_trace_jsonl(path)]

    def get_run_analytics(self, run_id: str) -> dict:
        return parse_trace_analytics(trace_file_path(self._project_root_for_run(run_id)))

    def get_run_artifacts(self, run_id: str) -> List[dict]:
        with self._lock:
            if run_id in self._artifacts_cache:
                return self._artifacts_cache[run_id]
        artifacts = discover_run_artifacts(self.project_root, run_id)
        data = [a.to_dict() for a in artifacts]
        with self._lock:
            self._artifacts_cache[run_id] = data
        return data

    def invalidate_artifacts(self, run_id: str) -> None:
        with self._lock:
            self._artifacts_cache.pop(run_id, None)

    def _experiment_file_path(self, project_root: Path) -> Path:
        return project_root / ".autoresearch" / "experiment.jsonl"

    def _load_experiments(self, force: bool = False) -> bool:
        path = self._experiment_file_path(self.project_root)
        if not path.is_file():
            if self._experiments:
                self._experiments = []
                self._experiments_mtime = 0.0
                return True
            return False
        mtime = path.stat().st_mtime
        if not force and mtime == self._experiments_mtime:
            return False
        experiments: List[dict] = []
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    obj = json.loads(stripped)
                    if isinstance(obj, dict):
                        experiments.append(obj)
                except json.JSONDecodeError:
                    continue
        except OSError:
            pass
        self._experiments = experiments
        self._experiments_mtime = mtime
        return True

    def get_experiments(self) -> List[dict]:
        with self._lock:
            self._load_experiments()
            return list(self._experiments)

    def get_run_experiments(self, run_id: str) -> List[dict]:
        path = self._experiment_file_path(self._project_root_for_run(run_id))
        experiments: List[dict] = []
        if not path.is_file():
            return experiments
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    obj = json.loads(stripped)
                    if isinstance(obj, dict):
                        experiments.append(obj)
                except json.JSONDecodeError:
                    continue
        except OSError:
            pass
        return experiments

    def on_experiment_changed(self) -> None:
        changed = False
        with self._lock:
            changed = self._load_experiments(force=True)
        if changed:
            self._schedule_publish({"type": "experiment_updated"})

    def _conversation_fingerprint(self) -> str:
        return conversation_sources_fingerprint(self.project_root, self.transcript_dirs)

    def _load_conversations(self, force: bool = False) -> bool:
        fp = self._conversation_fingerprint()
        if not force and fp == self._conversations_fingerprint:
            return False
        conversations = discover_conversations(self.project_root, self.transcript_dirs)
        self._conversations = [c.to_dict() for c in conversations]
        self._conversations_fingerprint = fp
        self._conversation_turns_cache.clear()
        return True

    def poll_conversations(self) -> None:
        """Fast poll for transcript append — publishes SSE when content changes."""
        fp = self._conversation_fingerprint()
        if fp == self._conversations_fingerprint:
            return
        latest_id: Optional[str] = None
        with self._lock:
            self._load_conversations(force=True)
            if self._conversations:
                latest_id = self._conversations[0]["id"]
        self._schedule_publish(
            {"type": "conversation_updated", "conversationId": latest_id}
        )

    def get_conversations(self) -> List[dict]:
        with self._lock:
            self._load_conversations()
            return list(self._conversations)

    def get_conversation(self, conversation_id: str) -> Optional[dict]:
        conversations = self.get_conversations()
        for conv in conversations:
            if conv["id"] == conversation_id:
                return conv
        return None

    def get_conversation_turns(self, conversation_id: str) -> List[dict]:
        with self._lock:
            if conversation_id in self._conversation_turns_cache:
                return self._conversation_turns_cache[conversation_id]
        conv = self.get_conversation(conversation_id)
        if not conv:
            return []
        turns = get_conversation_turns(Path(conv["path"]))
        with self._lock:
            self._conversation_turns_cache[conversation_id] = turns
        return turns

    def on_conversation_changed(self, conversation_id: Optional[str] = None) -> None:
        changed = False
        with self._lock:
            changed = self._load_conversations(force=True)
        if changed:
            payload: Dict[str, Any] = {"type": "conversation_updated"}
            if conversation_id:
                payload["conversationId"] = conversation_id
            elif self._conversations:
                payload["conversationId"] = self._conversations[0]["id"]
            self._schedule_publish(payload)

    def invalidate_run(self, run_id: str) -> None:
        with self._lock:
            self.iterations_cache.pop(run_id, None)
            self.summary_cache.pop(run_id, None)

    def get_run(self, run_id: str) -> Optional[RunInfo]:
        for r in self.runs:
            if r.run_id == run_id:
                return r
        return None

    def get_iterations(self, run_id: str) -> List[dict]:
        with self._lock:
            if run_id in self.iterations_cache:
                return self.iterations_cache[run_id]
        metric_direction, headers, iterations = parse_log_file(self.project_root, run_id)
        data = [it.to_dict() for it in iterations]
        with self._lock:
            self.iterations_cache[run_id] = data
            run = self.get_run(run_id)
            if run:
                self.summary_cache[run_id] = compute_summary(iterations, metric_direction or run.metric_direction)
        return data

    def get_summary(self, run_id: str) -> dict:
        with self._lock:
            if run_id in self.summary_cache:
                return self.summary_cache[run_id]
        self.get_iterations(run_id)
        with self._lock:
            return self.summary_cache.get(run_id, {})

    def refresh_git(self, force: bool = False) -> bool:
        now = time.time()
        if not force and now - self._last_git_poll < 5:
            return False

        by_project: Dict[str, List[ExperimentCommit]] = {}
        roots_by_project: Dict[str, Path] = {}
        for scan_root in discover_project_roots(self.project_root):
            project_id = (
                "."
                if scan_root == self.project_root
                else scan_root.relative_to(self.project_root).as_posix()
            )
            by_project[project_id] = list_experiment_commits(
                scan_root,
                project_id=project_id,
            )
            git_root = resolve_git_root(scan_root)
            if git_root is not None:
                roots_by_project[project_id] = git_root

        merged: List[ExperimentCommit] = []
        seen: set[str] = set()
        for commits in by_project.values():
            for commit in commits:
                if commit.hash in seen:
                    continue
                seen.add(commit.hash)
                merged.append(commit)
        merged.sort(key=lambda c: c.date, reverse=True)

        previous = [c.short_hash for c in self.git_commits]
        current = [c.short_hash for c in merged]
        changed = previous != current
        with self._lock:
            self._git_commits_by_project = by_project
            self._git_roots_by_project = roots_by_project
            self.git_commits = merged
            self._last_git_poll = now
        return changed

    def get_git_commits(self, project_id: Optional[str] = None) -> List[dict]:
        with self._lock:
            if project_id and project_id != "all":
                commits = self._git_commits_by_project.get(project_id, [])
                return [c.to_dict() for c in commits]
            return [c.to_dict() for c in self.git_commits]

    def get_commit_stat(self, commit_hash: str, project_id: Optional[str] = None) -> Optional[str]:
        candidates: List[Path] = []
        with self._lock:
            if project_id and project_id != "all":
                root = self._git_roots_by_project.get(project_id)
                if root is not None:
                    candidates.append(root)
            else:
                candidates.extend(self._git_roots_by_project.values())
                if not candidates:
                    candidates.append(self.project_root)

        for root in candidates:
            stat = commit_diff_stat(root, commit_hash)
            if stat:
                return stat
        return None

    async def publish(self, event: Dict[str, Any]) -> None:
        dead: List[asyncio.Queue] = []
        for q in list(self._subscribers):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                dead.append(q)
        for q in dead:
            self._subscribers.discard(q)

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=64)
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._subscribers.discard(q)

    def _schedule_publish(self, event: Dict[str, Any]) -> None:
        if self._loop is None or not self._loop.is_running():
            return
        asyncio.run_coroutine_threadsafe(self.publish(event), self._loop)

    def on_file_changed(self, rel_path: str) -> None:
        self.invalidate_run(rel_path)
        run_dir = str(Path(rel_path).parent)
        for run in self.runs:
            if run.run_id.startswith(run_dir):
                self.invalidate_artifacts(run.run_id)
        self.refresh_runs()
        run = self.get_run(rel_path)
        self._schedule_publish(
            {
                "type": "run_updated",
                "runId": rel_path,
                "iterationCount": run.row_count if run else 0,
            }
        )

    def on_trace_changed(self) -> None:
        changed = False
        with self._lock:
            changed = self._load_trace(force=True)
        if changed:
            self._schedule_publish({"type": "trace_updated"})

    def on_gemma4_trace_changed(self) -> None:
        self._schedule_publish({"type": "trace_updated", "traceKind": "gemma4"})

    def on_gemma3_trace_changed(self) -> None:
        self._schedule_publish({"type": "trace_updated", "traceKind": "gemma3"})

    def on_artifacts_changed(self, run_id: str) -> None:
        self.invalidate_artifacts(run_id)
        self._schedule_publish({"type": "trace_updated", "runId": run_id})

    def on_git_changed(self) -> None:
        self._schedule_publish({"type": "git_updated"})
