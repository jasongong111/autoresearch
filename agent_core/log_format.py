"""Human-readable formatting for skill agent trace events."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional

PHASE_META: Dict[str, Dict[str, str]] = {
    "user_request": {"tag": "USER", "tone": "user"},
    "model_request": {"tag": "MODEL REQUEST", "tone": "request"},
    "model_delta": {"tag": "STREAM", "tone": "stream"},
    "tool_call": {"tag": "TOOL CALL", "tone": "tool"},
    "tool_result": {"tag": "TOOL RESULT", "tone": "tool"},
    "assistant_message": {"tag": "ASSISTANT", "tone": "assistant"},
    "run_complete": {"tag": "COMPLETE", "tone": "complete"},
    "metrics": {"tag": "METRICS", "tone": "meta"},
    "error": {"tag": "ERROR", "tone": "error"},
}

TONE_COLORS: Dict[str, str] = {
    "user": "#60a5fa",
    "request": "#a78bfa",
    "stream": "#94a3b8",
    "tool": "#fbbf24",
    "assistant": "#4ade80",
    "complete": "#34d399",
    "error": "#f87171",
    "meta": "#9aa4b8",
}


def _short_time(timestamp: str) -> str:
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return parsed.strftime("%H:%M:%S")
    except ValueError:
        return timestamp[:8] if timestamp else "--:--:--"


def _clip(text: str, limit: int = 400) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _extract_text_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not content:
        return ""
    if isinstance(content, list):
        parts: List[str] = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(str(block.get("text", "")))
                elif "text" in block:
                    parts.append(str(block["text"]))
            elif hasattr(block, "text"):
                parts.append(str(block.text))
        return "".join(parts)
    return str(content)


def format_input_item(item: Dict[str, Any]) -> tuple[str, str]:
    item_type = str(item.get("type") or "")
    role = str(item.get("role") or "")

    if role == "user" or (item_type == "message" and role == "user"):
        return "USER", _clip(str(item.get("content") or ""))

    if role == "assistant" or item_type == "message":
        text = _extract_text_content(item.get("content"))
        return "ASSISTANT", _clip(text)

    if item_type == "function_call":
        name = str(item.get("name") or "unknown")
        args = str(item.get("arguments") or "{}")
        return "TOOL CALL", _clip(f"{name}({args})", 500)

    if item_type == "function_call_output":
        output = str(item.get("output") or "")
        return "TOOL RESULT", _clip(output, 500)

    if "content" in item:
        return role.upper() or "ITEM", _clip(_extract_text_content(item.get("content")))

    return item_type.upper() or "ITEM", _clip(json.dumps(item, ensure_ascii=False), 500)


def collapse_stream_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    collapsed: List[Dict[str, Any]] = []
    stream_buffer = ""
    stream_event: Optional[Dict[str, Any]] = None

    for event in events:
        phase = event.get("phase")
        if phase == "model_delta":
            delta = str((event.get("data") or {}).get("delta") or "")
            if not stream_event:
                stream_event = dict(event)
            stream_buffer += delta
            continue

        if stream_event is not None:
            collapsed.append(
                {
                    **stream_event,
                    "phase": "model_delta",
                    "data": {"delta": stream_buffer, "collapsed": True},
                }
            )
            stream_buffer = ""
            stream_event = None

        collapsed.append(event)

    if stream_event is not None:
        collapsed.append(
            {
                **stream_event,
                "phase": "model_delta",
                "data": {"delta": stream_buffer, "collapsed": True},
            }
        )

    return collapsed


def format_event_record(event: Dict[str, Any]) -> Dict[str, Any]:
    phase = str(event.get("phase") or "event")
    data = event.get("data") or {}
    meta = PHASE_META.get(phase, {"tag": phase.upper(), "tone": "meta"})
    timestamp = str(event.get("ts") or "")
    session_id = str(event.get("session_id") or "")

    record: Dict[str, Any] = {
        "time": _short_time(timestamp),
        "timestamp": timestamp,
        "session_id": session_id,
        "phase": phase,
        "tag": meta["tag"],
        "tone": meta["tone"],
        "color": TONE_COLORS.get(meta["tone"], TONE_COLORS["meta"]),
        "title": meta["tag"],
        "body": "",
        "details": [],
    }

    if phase == "user_request":
        record["body"] = str(data.get("message") or "")
        return record

    if phase == "model_request":
        agent = str(data.get("agent") or "agent")
        items = list(data.get("input") or [])
        record["title"] = f"{meta['tag']} · {agent} · {len(items)} items"
        record["details"] = [
            {"tag": tag, "body": body} for tag, body in (format_input_item(item) for item in items)
        ]
        instructions = str(data.get("instructions") or "")
        if instructions:
            record["details"].insert(
                0,
                {"tag": "SYSTEM", "body": _clip(instructions, 240)},
            )
        return record

    if phase == "model_delta":
        record["body"] = str(data.get("delta") or "")
        if data.get("collapsed"):
            record["title"] = "STREAM · collapsed"
        return record

    if phase == "tool_call":
        name = str(data.get("name") or "unknown")
        args = str(data.get("arguments") or "{}")
        record["body"] = f"{name}({args})"
        return record

    if phase == "tool_result":
        name = data.get("name")
        result = str(data.get("result") or data.get("output") or "")
        prefix = f"{name}: " if name else ""
        record["body"] = _clip(prefix + result, 800)
        return record

    if phase == "assistant_message":
        record["body"] = str(data.get("content") or "")
        return record

    if phase == "run_complete":
        status = str(data.get("status") or "finished")
        record["title"] = f"{meta['tag']} · {status}"
        record["body"] = str(data.get("answer") or "")
        metrics = data.get("metrics")
        if isinstance(metrics, dict):
            record["details"].append(
                {
                    "tag": "METRICS",
                    "body": (
                        f"latency={metrics.get('latency_ms', 0)}ms · "
                        f"prompt={metrics.get('prompt_tokens', 0)} · "
                        f"completion={metrics.get('completion_tokens', 0)} · "
                        f"total={metrics.get('total_tokens', 0)}"
                    ),
                }
            )
        return record

    if phase == "metrics":
        record["title"] = (
            f"{meta['tag']} · {data.get('latency_ms', 0)}ms · "
            f"total_tokens={data.get('total_tokens', 0)}"
        )
        record["body"] = (
            f"prompt_tokens={data.get('prompt_tokens', 0)} · "
            f"completion_tokens={data.get('completion_tokens', 0)} · "
            f"requests={data.get('requests', 0)}"
        )
        request_usage = data.get("request_usage") or []
        if request_usage:
            record["details"] = [
                {
                    "tag": f"REQUEST {index + 1}",
                    "body": (
                        f"prompt={entry.get('prompt_tokens', 0)} · "
                        f"completion={entry.get('completion_tokens', 0)} · "
                        f"total={entry.get('total_tokens', 0)}"
                    ),
                }
                for index, entry in enumerate(request_usage)
            ]
        return record

    if phase == "error":
        record["body"] = str(data.get("error") or "unknown error")
        return record

    record["body"] = _clip(json.dumps(data, ensure_ascii=False), 800)
    return record


def format_event_text(event: Dict[str, Any]) -> str:
    record = format_event_record(event)
    lines = [f"[{record['time']}] {record['title']}"]

    if record["details"]:
        for detail in record["details"]:
            tag = detail["tag"].ljust(12)
            body = detail["body"].replace("\n", "\n    ")
            lines.append(f"  {tag} {body}")
    elif record["body"]:
        body = record["body"].replace("\n", "\n  ")
        lines.append(f"  {body}")

    return "\n".join(lines)


def format_events_text(
    events: Iterable[Dict[str, Any]],
    *,
    collapse_stream: bool = True,
) -> str:
    event_list = list(events)
    if collapse_stream:
        event_list = collapse_stream_events(event_list)
    return "\n\n".join(format_event_text(event) for event in event_list)


def load_trace_events(
    trace_path: Path,
    *,
    session_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    if not trace_path.is_file():
        return []

    events: List[Dict[str, Any]] = []
    for line in trace_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if session_id and event.get("session_id") != session_id:
            continue
        events.append(event)
    return events


def iter_trace_text(
    trace_path: Path,
    *,
    session_id: Optional[str] = None,
    collapse_stream: bool = True,
) -> Iterator[str]:
    events = load_trace_events(trace_path, session_id=session_id)
    if collapse_stream:
        events = collapse_stream_events(events)
    for event in events:
        yield format_event_text(event)


class StreamLogBuffer:
    """Collapse streaming token events for cleaner live output."""

    def __init__(self) -> None:
        self._parts: List[str] = []
        self._event: Optional[Dict[str, Any]] = None

    def append(self, event: Dict[str, Any]) -> None:
        if self._event is None:
            self._event = dict(event)
        self._parts.append(str((event.get("data") or {}).get("delta") or ""))

    def flush(self) -> Optional[Dict[str, Any]]:
        if self._event is None:
            return None
        merged = dict(self._event)
        merged["data"] = {
            "delta": "".join(self._parts),
            "collapsed": True,
        }
        self._parts = []
        self._event = None
        return merged
