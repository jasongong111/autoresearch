"""JSON-file persistent store for run configs and instances."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Dict, List, Optional

from .models import RunConfig, RunInstance


class OrchestratorStore:
    """File-backed store for run configurations and execution history.

    Uses JSON files under ``~/.autoresearch/orchestrator/`` (or a custom path).
    No external database dependency.
    """

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        if base_dir is None:
            base_dir = Path.home() / ".autoresearch" / "orchestrator"
        self.base_dir = base_dir
        self.configs_dir = self.base_dir / "configs"
        self.instances_dir = self.base_dir / "instances"
        self.configs_dir.mkdir(parents=True, exist_ok=True)
        self.instances_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    # --- RunConfig CRUD ---

    def list_configs(self) -> List[RunConfig]:
        with self._lock:
            configs: List[RunConfig] = []
            for path in sorted(self.configs_dir.glob("*.json")):
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    configs.append(RunConfig(**data))
                except Exception:
                    continue
            return configs

    def get_config(self, config_id: str) -> Optional[RunConfig]:
        path = self.configs_dir / f"{config_id}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return RunConfig(**data)
        except Exception:
            return None

    def save_config(self, config: RunConfig) -> None:
        path = self.configs_dir / f"{config.id}.json"
        with self._lock:
            path.write_text(config.model_dump_json(indent=2), encoding="utf-8")

    def delete_config(self, config_id: str) -> bool:
        path = self.configs_dir / f"{config_id}.json"
        with self._lock:
            if path.exists():
                path.unlink()
                return True
            return False

    # --- RunInstance CRUD ---

    def list_instances(self) -> List[RunInstance]:
        with self._lock:
            instances: List[RunInstance] = []
            for path in sorted(self.instances_dir.glob("*.json"), reverse=True):
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    instances.append(RunInstance(**data))
                except Exception:
                    continue
            return instances

    def get_instance(self, instance_id: str) -> Optional[RunInstance]:
        path = self.instances_dir / f"{instance_id}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return RunInstance(**data)
        except Exception:
            return None

    def save_instance(self, instance: RunInstance) -> None:
        path = self.instances_dir / f"{instance.id}.json"
        with self._lock:
            path.write_text(instance.model_dump_json(indent=2), encoding="utf-8")

    def delete_instance(self, instance_id: str) -> bool:
        path = self.instances_dir / f"{instance_id}.json"
        with self._lock:
            if path.exists():
                path.unlink()
                return True
            return False
