"""Real-time structured logging for skill agent runs."""

from __future__ import annotations

import json
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .log_format import StreamLogBuffer, format_event_record, format_event_text

LogCallback = Callable[[Dict[str, Any]], None]


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "model_dump"):
        try:
            return _json_safe(value.model_dump(mode="json"))
        except TypeError:
            return _json_safe(value.model_dump())
    if hasattr(value, "to_dict"):
        return _json_safe(value.to_dict())
    return str(value)


def serialize_model_input(items: List[Any]) -> List[Any]:
    serialized: List[Any] = []
    for item in items:
        if isinstance(item, dict):
            serialized.append(_json_safe(item))
            continue
        if hasattr(item, "model_dump"):
            try:
                serialized.append(_json_safe(item.model_dump(mode="json")))
            except TypeError:
                serialized.append(_json_safe(item.model_dump()))
            continue
        serialized.append(str(item))
    return serialized


def _attach_formatted(event: Dict[str, Any]) -> Dict[str, Any]:
    enriched = dict(event)
    enriched["formatted"] = format_event_record(event)
    return enriched


class AgentLogger:
    """Emit request/response events to stderr, JSONL, and optional callbacks."""

    def __init__(
        self,
        *,
        session_id: str,
        trace_path: Path,
        stderr: bool = True,
        file: bool = True,
        on_event: Optional[LogCallback] = None,
    ) -> None:
        self.session_id = session_id
        self.trace_path = trace_path
        self.stderr = stderr
        self.file = file
        self.on_event = on_event
        self._lock = threading.Lock()
        self._stream_buffer = StreamLogBuffer()
        if self.file:
            self.trace_path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, phase: str, data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        event = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "phase": phase,
            "data": _json_safe(data or {}),
        }

        if phase == "model_delta":
            self._stream_buffer.append(event)
            if self.file:
                self._write_file(event)
            return []

        display_events: List[Dict[str, Any]] = []
        flushed = self._stream_buffer.flush()
        if flushed is not None:
            display_events.append(self._publish(flushed))

        display_events.append(self._publish(event, write_file=True, raw_event=event))
        return display_events

    def finalize(self) -> List[Dict[str, Any]]:
        flushed = self._stream_buffer.flush()
        if flushed is None:
            return []
        return [self._publish(flushed)]

    def _publish(
        self,
        event: Dict[str, Any],
        *,
        write_file: bool = False,
        raw_event: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        enriched = _attach_formatted(event)
        if self.stderr:
            print(format_event_text(event), file=sys.stderr, flush=True)
            print(file=sys.stderr, flush=True)
        if write_file and raw_event is not None:
            self._write_file(raw_event)
        elif write_file:
            self._write_file(event)
        if self.on_event is not None:
            self.on_event(enriched)
        return enriched

    def _write_file(self, event: Dict[str, Any]) -> None:
        with self._lock:
            with self.trace_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")
