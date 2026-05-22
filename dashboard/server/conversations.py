"""Agent conversation parsing — Cursor transcripts and project-local JSONL."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

CONVERSATION_PATH = ".autoresearch/conversation.jsonl"
MCP_TOOL_NAMES = frozenset({"CallMcpTool", "call_mcp_tool", "mcp_tool"})


@dataclass
class ConversationInfo:
    conversation_id: str
    title: str
    path: str
    last_modified: float
    turn_count: int
    kind: str  # cursor, subagent, local
    parent_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.conversation_id,
            "title": self.title,
            "path": self.path,
            "lastModified": self.last_modified,
            "turnCount": self.turn_count,
            "kind": self.kind,
            "parentId": self.parent_id,
        }


@dataclass
class ConversationTurn:
    index: int
    role: str
    blocks: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {"index": self.index, "role": self.role, "blocks": self.blocks}


def conversation_file_path(project_root: Path) -> Path:
    return project_root / CONVERSATION_PATH


def cursor_transcripts_dir(project_root: Path) -> Optional[Path]:
    """Guess Cursor agent-transcripts path from project root."""
    resolved = project_root.resolve()
    slug = str(resolved).lstrip("/").replace("/", "-")
    if resolved.drive:  # Windows e.g. C:\foo -> C:-foo
        slug = str(resolved).replace("\\", "-").replace(":", "-").lstrip("-")
    path = Path.home() / ".cursor" / "projects" / slug / "agent-transcripts"
    return path if path.is_dir() else None


def resolve_transcript_dirs(
    project_root: Path, explicit_dirs: Optional[Sequence[Path]] = None
) -> List[Path]:
    dirs: List[Path] = []
    seen: set[str] = set()

    def add(path: Path) -> None:
        resolved = path.resolve()
        key = str(resolved)
        if key not in seen and resolved.is_dir():
            seen.add(key)
            dirs.append(resolved)

    if explicit_dirs:
        for d in explicit_dirs:
            add(d)
    cursor_dir = cursor_transcripts_dir(project_root)
    if cursor_dir:
        add(cursor_dir)
    return dirs


def discover_conversations(
    project_root: Path, transcript_dirs: Sequence[Path]
) -> List[ConversationInfo]:
    conversations: List[ConversationInfo] = []

    local_path = conversation_file_path(project_root)
    if local_path.is_file():
        conversations.append(_conversation_info_from_path("local", local_path, "local", None))

    for tdir in transcript_dirs:
        if not tdir.is_dir():
            continue
        for session_dir in sorted(tdir.iterdir()):
            if not session_dir.is_dir():
                continue
            session_id = session_dir.name
            main_file = session_dir / f"{session_id}.jsonl"
            if main_file.is_file():
                conversations.append(
                    _conversation_info_from_path(session_id, main_file, "cursor", None)
                )
            subagents = session_dir / "subagents"
            if subagents.is_dir():
                for sub_file in sorted(subagents.glob("*.jsonl")):
                    sub_id = f"{session_id}/subagents/{sub_file.stem}"
                    conversations.append(
                        _conversation_info_from_path(
                            sub_id,
                            sub_file,
                            "subagent",
                            session_id,
                        )
                    )

    conversations.sort(key=lambda c: c.last_modified, reverse=True)
    return conversations


def _conversation_info_from_path(
    conversation_id: str,
    path: Path,
    kind: str,
    parent_id: Optional[str],
) -> ConversationInfo:
    stat = path.stat()
    turns = parse_transcript_jsonl(path)
    title = _title_from_turns(turns, conversation_id, kind)
    return ConversationInfo(
        conversation_id=conversation_id,
        title=title,
        path=str(path),
        last_modified=stat.st_mtime,
        turn_count=len(turns),
        kind=kind,
        parent_id=parent_id,
    )


def _title_from_turns(turns: List[ConversationTurn], conversation_id: str, kind: str) -> str:
    for turn in turns:
        if turn.role != "user":
            continue
        for block in turn.blocks:
            if block.get("type") == "text" and block.get("text"):
                text = _strip_user_query(str(block["text"]))
                first_line = text.split("\n", 1)[0].strip()
                if first_line:
                    if len(first_line) > 72:
                        return first_line[:69] + "..."
                    return first_line
    if kind == "subagent":
        return f"Subagent {conversation_id.rsplit('/', 1)[-1][:8]}"
    return conversation_id[:8] + "…"


def parse_transcript_jsonl(path: Path) -> List[ConversationTurn]:
    if not path.is_file():
        return []
    turns: List[ConversationTurn] = []
    index = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict):
            continue
        turn = _parse_turn_line(obj, index)
        if turn is None:
            continue
        turns.append(turn)
        index += 1
    return turns


def _parse_turn_line(obj: Dict[str, Any], index: int) -> Optional[ConversationTurn]:
    role = str(obj.get("role") or "").lower()
    if role not in ("user", "assistant", "tool", "system"):
        return None

    blocks: List[Dict[str, Any]] = []
    message = obj.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    normalized = normalize_content_block(item)
                    if normalized:
                        blocks.extend(normalized if isinstance(normalized, list) else [normalized])
        elif isinstance(content, str) and content.strip():
            blocks.append({"type": "text", "text": content.strip()})

    # Flat formats: tool_result at top level
    if role == "tool" and not blocks:
        blocks.append(
            {
                "type": "tool_result",
                "toolName": obj.get("name") or obj.get("tool_name") or "tool",
                "content": obj.get("content") or obj.get("result") or obj,
            }
        )

    if not blocks:
        return None
    return ConversationTurn(index=index, role=role, blocks=blocks)


def normalize_content_block(block: Dict[str, Any]) -> Optional[Dict[str, Any] | List[Dict[str, Any]]]:
    block_type = str(block.get("type") or "").lower()

    if block_type == "text":
        text = str(block.get("text") or "").strip()
        if not text:
            return None
        if text == "[REDACTED]":
            return {"type": "thinking", "text": "", "redacted": True}
        return {"type": "text", "text": _strip_user_query(text) if "<user_query>" in text else text}

    if block_type in ("thinking", "reasoning", "thought"):
        text = str(block.get("text") or block.get("thinking") or "").strip()
        return {"type": "thinking", "text": text, "redacted": text == "[REDACTED]"}

    if block_type == "tool_use":
        name = str(block.get("name") or block.get("tool_name") or "tool")
        tool_input = block.get("input")
        if tool_input is None:
            tool_input = block.get("arguments") or {}
        if not isinstance(tool_input, dict):
            tool_input = {"value": tool_input}

        if name in MCP_TOOL_NAMES or "server" in tool_input or "toolName" in tool_input:
            return {
                "type": "mcp",
                "server": tool_input.get("server") or tool_input.get("mcp_server") or "",
                "toolName": tool_input.get("toolName") or tool_input.get("tool_name") or name,
                "arguments": tool_input.get("arguments") or {
                    k: v for k, v in tool_input.items() if k not in ("server", "toolName", "tool_name")
                },
            }

        result: Dict[str, Any] = {
            "type": "tool_use",
            "name": name,
            "input": tool_input,
        }
        if name == "Task" and isinstance(tool_input, dict):
            result["subagentType"] = tool_input.get("subagent_type") or tool_input.get("subagentType")
            result["description"] = tool_input.get("description") or ""
        return result

    if block_type in ("tool_result", "tool_result_error"):
        return {
            "type": "tool_result",
            "toolName": block.get("name") or block.get("tool_name") or block.get("tool_use_id") or "tool",
            "content": block.get("content") or block.get("result") or block.get("output") or "",
            "isError": block_type == "tool_result_error" or bool(block.get("is_error")),
        }

    # Unknown block — preserve as JSON for debugging
    if block:
        return {"type": "unknown", "raw": block}
    return None


def _strip_user_query(text: str) -> str:
    text = re.sub(r"^<user_query>\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*</user_query>\s*$", "", text, flags=re.IGNORECASE)
    return text.strip()


def get_conversation_turns(path: Path) -> List[dict]:
    return [t.to_dict() for t in parse_transcript_jsonl(path)]
