"""Agent conversation parsing — Cursor transcripts and project-local JSONL."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

CONVERSATION_PATH = ".autoresearch/conversation.jsonl"
MCP_TOOL_NAMES = frozenset({"CallMcpTool", "call_mcp_tool", "mcp_tool"})

CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"


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


def conversation_id_for_project(workspace_root: Path, project_path: str) -> str:
    """Stable dashboard conversation id for a project's local JSONL mirror."""
    workspace_root = workspace_root.resolve()
    task = Path(project_path).resolve()
    if task == workspace_root:
        return "local"
    try:
        return f"{task.relative_to(workspace_root).as_posix()}/local"
    except ValueError:
        return "local"


def cursor_transcripts_dir(project_root: Path) -> Optional[Path]:
    """Guess Cursor agent-transcripts path from project root."""
    resolved = project_root.resolve()
    slug = str(resolved).lstrip("/").replace("/", "-")
    if resolved.drive:  # Windows e.g. C:\foo -> C:-foo
        slug = str(resolved).replace("\\", "-").replace(":", "-").lstrip("-")
    path = Path.home() / ".cursor" / "projects" / slug / "agent-transcripts"
    return path if path.is_dir() else None


def claude_transcripts_dir(project_root: Path) -> Optional[Path]:
    """Guess Claude Code projects path from project root."""
    resolved = project_root.resolve()
    # Claude uses the resolved path with slashes replaced by dashes, prefixed with a dash
    # e.g. /Users/jasongong/Desktop/autoresearch -> -Users-jasongong-Desktop-autoresearch
    slug = "-" + str(resolved).lstrip("/").replace("/", "-")
    if resolved.drive:  # Windows e.g. C:\foo -> -C--foo
        slug = "-" + str(resolved).replace("\\", "-").replace(":", "-").lstrip("-")
    path = CLAUDE_PROJECTS_DIR / slug
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
    claude_dir = claude_transcripts_dir(project_root)
    if claude_dir:
        add(claude_dir)
    return dirs


def discover_conversations(
    project_root: Path, transcript_dirs: Sequence[Path]
) -> List[ConversationInfo]:
    from .discovery import discover_project_roots

    conversations: List[ConversationInfo] = []
    seen_local: set[str] = set()
    project_root = project_root.resolve()

    for root in discover_project_roots(project_root):
        local_path = conversation_file_path(root)
        if not local_path.is_file():
            continue
        key = str(local_path.resolve())
        if key in seen_local:
            continue
        seen_local.add(key)
        if root == project_root:
            conv_id = "local"
        else:
            conv_id = f"{root.relative_to(project_root).as_posix()}/local"
        conversations.append(_conversation_info_from_path(conv_id, local_path, "local", None))

    for tdir in transcript_dirs:
        if not tdir.is_dir():
            continue
        # Claude Code transcript dir: ~/.claude/projects/<slug>/
        if tdir.parent.parent.name == ".claude" and tdir.parent.name == "projects":
            for jsonl_file in sorted(tdir.glob("*.jsonl")):
                if not jsonl_file.is_file():
                    continue
                session_id = jsonl_file.stem
                conversations.append(
                    _conversation_info_from_path(session_id, jsonl_file, "claude", None)
                )
            continue
        # Cursor transcript dir
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
    raw = path.read_text(encoding="utf-8").splitlines()
    # Detect Claude Code format by sampling first few non-empty lines
    claude_markers = ("sessionId", "userType", "entrypoint", "uuid", "version")
    checked = 0
    for line in raw:
        stripped = line.strip()
        if not stripped:
            continue
        checked += 1
        if checked > 10:
            break
        try:
            sample = json.loads(stripped)
        except json.JSONDecodeError:
            break
        if isinstance(sample, dict) and "type" in sample:
            # Claude Code transcripts have sessionId / uuid / userType markers
            if any(m in sample for m in claude_markers):
                return _parse_claude_transcript_jsonl(raw)
            # If the first line has 'type' but no markers, keep checking more lines
            continue
    # Default to generic / Cursor format
    turns: List[ConversationTurn] = []
    index = 0
    for line in raw:
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


def _parse_claude_transcript_jsonl(lines: List[str]) -> List[ConversationTurn]:
    """Parse Claude Code session JSONL into ConversationTurns."""
    turns: List[ConversationTurn] = []
    index = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict):
            continue
        turn = _parse_claude_message(obj, index)
        if turn is None:
            continue
        turns.append(turn)
        index += 1
    return turns


def _parse_claude_message(obj: Dict[str, Any], index: int) -> Optional[ConversationTurn]:
    msg_type = str(obj.get("type") or "").lower()
    # Skip non-conversation records
    if msg_type in ("ai-title", "last-prompt", "file-history-snapshot"):
        return None

    # user / assistant / system / attachment
    if msg_type == "attachment":
        # Treat attachments as user turns with file info
        blocks: List[Dict[str, Any]] = []
        attachment = obj.get("attachment") or {}
        file_path = attachment.get("filePath") or attachment.get("path") or ""
        if file_path:
            blocks.append({"type": "text", "text": f"[Attachment: {file_path}]"})
        if not blocks:
            return None
        return ConversationTurn(index=index, role="user", blocks=blocks)

    if msg_type == "system":
        subtype = str(obj.get("subtype") or "").lower()
        content = str(obj.get("content") or "").strip()
        if not content:
            return None
        return ConversationTurn(
            index=index,
            role="system",
            blocks=[{"type": "text", "text": f"[{subtype}] {content}"}],
        )

    if msg_type not in ("user", "assistant"):
        return None

    role = msg_type
    message = obj.get("message")
    if not isinstance(message, dict):
        return None

    content = message.get("content")
    blocks = _parse_claude_content(content, role)

    # If this is a user message with toolUseResult but no blocks, synthesize from toolUseResult
    if role == "user" and not blocks and "toolUseResult" in obj:
        tool_result = obj["toolUseResult"]
        if isinstance(tool_result, dict):
            result_type = tool_result.get("type", "text")
            if result_type == "file" and "file" in tool_result:
                file_info = tool_result["file"]
                file_path = file_info.get("filePath") or file_info.get("path") or ""
                content_text = file_info.get("content") or ""
                blocks.append({
                    "type": "tool_result",
                    "toolName": file_path or "tool",
                    "content": content_text,
                    "isError": False,
                })
            else:
                result_content = tool_result.get("content") or ""
                blocks.append({
                    "type": "tool_result",
                    "toolName": "tool",
                    "content": result_content,
                    "isError": False,
                })

    if not blocks:
        return None

    # Map tool-result-only user messages to role="tool" for UI consistency
    if role == "user" and all(b.get("type") == "tool_result" for b in blocks):
        role = "tool"

    return ConversationTurn(index=index, role=role, blocks=blocks)


def _parse_claude_content(content: Any, role: str) -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = []
    if isinstance(content, str):
        text = content.strip()
        if text:
            blocks.append({"type": "text", "text": text})
        return blocks
    if not isinstance(content, list):
        return blocks
    for item in content:
        if not isinstance(item, dict):
            continue
        block_type = str(item.get("type") or "").lower()
        if block_type == "text":
            text = str(item.get("text") or "").strip()
            if text:
                blocks.append({"type": "text", "text": _strip_user_query(text) if "<user_query>" in text else text})
        elif block_type == "thinking":
            text = str(item.get("thinking") or item.get("text") or "").strip()
            blocks.append({"type": "thinking", "text": text, "redacted": text == "[REDACTED]"})
        elif block_type == "tool_use":
            name = str(item.get("name") or item.get("tool_name") or "tool")
            tool_input = item.get("input")
            if tool_input is None:
                tool_input = item.get("arguments") or {}
            if not isinstance(tool_input, dict):
                tool_input = {"value": tool_input}
            blocks.append({"type": "tool_use", "name": name, "input": tool_input})
        elif block_type == "tool_result":
            tool_name = str(item.get("name") or item.get("tool_name") or item.get("tool_use_id") or "tool")
            result_content = item.get("content") or item.get("result") or item.get("output") or ""
            is_error = bool(item.get("is_error") or item.get("isError"))
            blocks.append({"type": "tool_result", "toolName": tool_name, "content": result_content, "isError": is_error})
        elif block_type == "image":
            blocks.append({"type": "unknown", "raw": item})
        else:
            blocks.append({"type": "unknown", "raw": item})
    return blocks


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


def conversation_sources_fingerprint(
    project_root: Path, transcript_dirs: Sequence[Path]
) -> str:
    """Stable fingerprint from mtimes + sizes for live conversation polling."""
    from .discovery import discover_project_roots

    parts: List[str] = []
    project_root = project_root.resolve()
    for root in discover_project_roots(project_root):
        local = conversation_file_path(root)
        if local.is_file():
            try:
                stat = local.stat()
                parts.append(f"{local.resolve()}:{stat.st_mtime_ns}:{stat.st_size}")
            except OSError:
                continue
    for tdir in transcript_dirs:
        if not tdir.is_dir():
            continue
        # Claude Code dir: flat jsonl files
        if tdir.parent.parent.name == ".claude" and tdir.parent.name == "projects":
            for path in sorted(tdir.glob("*.jsonl")):
                try:
                    stat = path.stat()
                    parts.append(f"{path.resolve()}:{stat.st_mtime_ns}:{stat.st_size}")
                except OSError:
                    continue
            continue
        # Cursor dir: nested session dirs
        for path in sorted(tdir.rglob("*.jsonl")):
            try:
                stat = path.stat()
                parts.append(f"{path.resolve()}:{stat.st_mtime_ns}:{stat.st_size}")
            except OSError:
                continue
    return "|".join(parts)
