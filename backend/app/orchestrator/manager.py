"""Run lifecycle manager — create config → spawn → monitor → stop."""

from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from backend.app.core.conversations import conversation_id_for_project

from .cursor_runner import run_cursor_agent
from .executor import prepare_run_workspace, spawn_run
from .models import RunConfig, RunInstance
from .store import OrchestratorStore

TAIL_LINES = 250


@dataclass
class _CursorJob:
    thread: threading.Thread
    cancel: threading.Event
    run_ref: Dict[str, Any] = field(default_factory=dict)


class RunManager:
    """Manages run configurations, instances, and background polling."""

    def __init__(
        self,
        store: Optional[OrchestratorStore] = None,
        event_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        workspace_root: Optional[Path] = None,
    ) -> None:
        self.store = store or OrchestratorStore()
        self.event_callback = event_callback
        self.workspace_root = (workspace_root or Path.cwd()).resolve()
        self._processes: Dict[str, subprocess.Popen] = {}
        self._cursor_jobs: Dict[str, _CursorJob] = {}
        self._lock = threading.Lock()
        self._poll_thread: Optional[threading.Thread] = None
        self._stop_polling = threading.Event()

    def start_polling(self) -> None:
        """Start the background thread that checks running processes."""
        if self._poll_thread is not None and self._poll_thread.is_alive():
            return
        self._stop_polling.clear()
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

    def stop_polling(self) -> None:
        """Signal the polling thread to stop."""
        self._stop_polling.set()
        if self._poll_thread is not None:
            self._poll_thread.join(timeout=2)

    def _publish(self, event: Dict[str, Any]) -> None:
        if self.event_callback:
            self.event_callback(event)

    def _poll_loop(self) -> None:
        while not self._stop_polling.is_set():
            self._tick()
            time.sleep(2.0)

    def _tick(self) -> None:
        with self._lock:
            finished: List[str] = []
            for instance_id, proc in list(self._processes.items()):
                instance = self.store.get_instance(instance_id)
                if instance is None:
                    finished.append(instance_id)
                    continue

                return_code = proc.poll()

                if return_code is not None:
                    instance.status = "completed" if return_code == 0 else "failed"
                    instance.exit_code = return_code
                    instance.completed_at = datetime.utcnow()
                    instance.pid = None
                    self.store.save_instance(instance)
                    finished.append(instance_id)
                    self._publish(
                        {
                            "type": "run_updated",
                            "instanceId": instance_id,
                            "status": instance.status,
                            "exitCode": return_code,
                        }
                    )
                else:
                    instance.pid = proc.pid
                    self.store.save_instance(instance)

            for instance_id in finished:
                self._processes.pop(instance_id, None)

    def create_config(self, **kwargs: Any) -> RunConfig:
        config = RunConfig(**kwargs)
        self.store.save_config(config)
        return config

    def update_config(self, config_id: str, **kwargs: Any) -> Optional[RunConfig]:
        config = self.store.get_config(config_id)
        if config is None:
            return None
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        config.updated_at = datetime.utcnow()
        self.store.save_config(config)
        return config

    def start_run(self, config_id: str) -> Optional[RunInstance]:
        config = self.store.get_config(config_id)
        if config is None:
            return None

        instance = RunInstance(
            config_id=config_id,
            status="running",
            started_at=datetime.utcnow(),
            project_path=config.project_path,
            conversation_id=conversation_id_for_project(self.workspace_root, config.project_path),
        )
        self.store.save_instance(instance)

        try:
            if config.runner == "cursor":
                prepare_run_workspace(config)
                self._start_cursor_run(instance.id, config)
                self._publish(
                    {
                        "type": "run_started",
                        "instanceId": instance.id,
                        "configId": config_id,
                        "runner": "cursor",
                        "conversationId": instance.conversation_id,
                        "projectPath": instance.project_path,
                    }
                )
                return instance

            proc = spawn_run(instance, config)
        except Exception as exc:
            instance.status = "failed"
            instance.completed_at = datetime.utcnow()
            instance.stderr_tail = [str(exc)]
            self.store.save_instance(instance)
            self._publish(
                {
                    "type": "run_updated",
                    "instanceId": instance.id,
                    "status": "failed",
                    "error": str(exc),
                }
            )
            return instance

        with self._lock:
            self._processes[instance.id] = proc
            instance.pid = proc.pid
            self.store.save_instance(instance)

        self._start_readers(instance.id, proc)

        self._publish(
            {
                "type": "run_started",
                "instanceId": instance.id,
                "configId": config_id,
                "pid": proc.pid,
                "conversationId": instance.conversation_id,
                "projectPath": instance.project_path,
            }
        )
        return instance

    def _append_output(self, instance_id: str, stream: str, line: str) -> None:
        instance = self.store.get_instance(instance_id)
        if instance is None:
            return
        tail = instance.stdout_tail if stream == "stdout" else instance.stderr_tail
        tail.append(line)
        if len(tail) > TAIL_LINES:
            tail = tail[-TAIL_LINES:]
        if stream == "stdout":
            instance.stdout_tail = tail
        else:
            instance.stderr_tail = tail
        self.store.save_instance(instance)
        self._publish(
            {
                "type": "run_output",
                "instanceId": instance_id,
                "stream": stream,
                "line": line,
            }
        )

    def _bind_cursor_conversation(self, instance_id: str, agent_id: str, cursor_run_id: str) -> None:
        instance = self.store.get_instance(instance_id)
        if instance is None:
            return
        instance.cursor_agent_id = agent_id
        instance.conversation_id = agent_id
        self.store.save_instance(instance)
        self._publish(
            {
                "type": "instance_updated",
                "instanceId": instance_id,
                "conversationId": agent_id,
                "cursorAgentId": agent_id,
                "cursorRunId": cursor_run_id,
                "status": instance.status,
            }
        )

    def _start_cursor_run(self, instance_id: str, config: RunConfig) -> None:
        cancel = threading.Event()
        job = _CursorJob(thread=threading.Thread(daemon=True), cancel=cancel)

        def worker() -> None:
            exit_code, error = run_cursor_agent(
                config,
                on_line=lambda stream, line: self._append_output(instance_id, stream, line),
                cancel_event=cancel,
                run_ref=job.run_ref,
                on_agent_started=lambda agent_id, cursor_run_id: self._bind_cursor_conversation(
                    instance_id, agent_id, cursor_run_id
                ),
            )
            instance = self.store.get_instance(instance_id)
            if instance is None:
                return

            if cancel.is_set() and exit_code == 130:
                instance.status = "stopped"
            elif exit_code == 0:
                instance.status = "completed"
            else:
                instance.status = "failed"
                if error:
                    instance.stderr_tail.append(error)
                    if len(instance.stderr_tail) > TAIL_LINES:
                        instance.stderr_tail = instance.stderr_tail[-TAIL_LINES:]

            instance.exit_code = exit_code
            instance.completed_at = datetime.utcnow()
            instance.pid = None
            self.store.save_instance(instance)

            with self._lock:
                self._cursor_jobs.pop(instance_id, None)

            self._publish(
                {
                    "type": "run_updated",
                    "instanceId": instance_id,
                    "status": instance.status,
                    "exitCode": exit_code,
                    "error": error,
                }
            )

        job.thread = threading.Thread(target=worker, daemon=True)
        with self._lock:
            self._cursor_jobs[instance_id] = job
        job.thread.start()

    def _start_readers(self, instance_id: str, proc: subprocess.Popen) -> None:
        def read_stdout() -> None:
            if proc.stdout is None:
                return
            for line in proc.stdout:
                self._append_output(instance_id, "stdout", line.rstrip("\n"))

        def read_stderr() -> None:
            if proc.stderr is None:
                return
            for line in proc.stderr:
                self._append_output(instance_id, "stderr", line.rstrip("\n"))

        threading.Thread(target=read_stdout, daemon=True).start()
        threading.Thread(target=read_stderr, daemon=True).start()

    def stop_run(self, instance_id: str) -> bool:
        with self._lock:
            cursor_job = self._cursor_jobs.get(instance_id)
            proc = self._processes.get(instance_id)

        if cursor_job is not None:
            cursor_job.cancel.set()
            run = cursor_job.run_ref.get("run")
            if run is not None and run.supports("cancel"):
                try:
                    run.cancel()
                except Exception:
                    pass
            instance = self.store.get_instance(instance_id)
            if instance is not None and instance.status == "running":
                instance.status = "stopped"
                instance.completed_at = datetime.utcnow()
                instance.pid = None
                self.store.save_instance(instance)
            self._publish({"type": "run_stopped", "instanceId": instance_id})
            return True

        if proc is None:
            instance = self.store.get_instance(instance_id)
            if instance is not None and instance.status == "running" and instance.pid:
                try:
                    os.kill(instance.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                instance.status = "stopped"
                instance.completed_at = datetime.utcnow()
                instance.pid = None
                self.store.save_instance(instance)
                self._publish(
                    {
                        "type": "run_stopped",
                        "instanceId": instance_id,
                    }
                )
                return True
            return False

        try:
            proc.terminate()
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

        instance = self.store.get_instance(instance_id)
        if instance is not None:
            instance.status = "stopped"
            instance.completed_at = datetime.utcnow()
            instance.pid = None
            self.store.save_instance(instance)

        with self._lock:
            self._processes.pop(instance_id, None)

        self._publish(
            {
                "type": "run_stopped",
                "instanceId": instance_id,
            }
        )
        return True

    def list_configs(self) -> List[RunConfig]:
        return self.store.list_configs()

    def get_config(self, config_id: str) -> Optional[RunConfig]:
        return self.store.get_config(config_id)

    def delete_config(self, config_id: str) -> bool:
        return self.store.delete_config(config_id)

    def list_instances(self) -> List[RunInstance]:
        return self.store.list_instances()

    def get_instance(self, instance_id: str) -> Optional[RunInstance]:
        return self.store.get_instance(instance_id)
