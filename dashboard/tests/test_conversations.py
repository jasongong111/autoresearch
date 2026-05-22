"""Tests for agent conversation parsing."""

import json
from pathlib import Path

from dashboard.server.conversations import (
    conversation_sources_fingerprint,
    discover_conversations,
    normalize_content_block,
    parse_transcript_jsonl,
    resolve_transcript_dirs,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_normalize_tool_use():
    block = normalize_content_block(
        {"type": "tool_use", "name": "Read", "input": {"path": "/tmp/foo.py"}}
    )
    assert block["type"] == "tool_use"
    assert block["name"] == "Read"


def test_normalize_mcp():
    block = normalize_content_block(
        {
            "type": "tool_use",
            "name": "CallMcpTool",
            "input": {
                "server": "user-linear",
                "toolName": "search",
                "arguments": {"query": "bug"},
            },
        }
    )
    assert block["type"] == "mcp"
    assert block["server"] == "user-linear"
    assert block["toolName"] == "search"


def test_normalize_thinking_redacted():
    block = normalize_content_block({"type": "text", "text": "[REDACTED]"})
    assert block["type"] == "thinking"
    assert block["redacted"] is True


def test_parse_transcript_fixture():
    turns = parse_transcript_jsonl(FIXTURES / "conversation.jsonl")
    assert len(turns) >= 2
    assert turns[0].role == "user"
    assert any(b["type"] == "text" for b in turns[0].blocks)
    assistant = next(t for t in turns if t.role == "assistant")
    assert any(b["type"] in ("tool_use", "text", "thinking") for b in assistant.blocks)


def test_discover_conversations_local(tmp_path: Path):
    conv_dir = tmp_path / ".autoresearch"
    conv_dir.mkdir()
    (conv_dir / "conversation.jsonl").write_text(
        json.dumps(
            {
                "role": "user",
                "message": {"content": [{"type": "text", "text": "Hello agent"}]},
            }
        )
        + "\n"
    )
    found = discover_conversations(tmp_path, [])
    assert len(found) == 1
    assert found[0].conversation_id == "local"
    assert found[0].turn_count == 1


def test_resolve_transcript_dirs_explicit(tmp_path: Path):
    explicit = tmp_path / "transcripts"
    explicit.mkdir()
    dirs = resolve_transcript_dirs(tmp_path, [explicit])
    assert explicit.resolve() in dirs


def test_conversation_fingerprint_detects_append(tmp_path: Path):
    conv_dir = tmp_path / ".autoresearch"
    conv_dir.mkdir()
    path = conv_dir / "conversation.jsonl"
    path.write_text(
        json.dumps(
            {
                "role": "user",
                "message": {"content": [{"type": "text", "text": "Hello"}]},
            }
        )
        + "\n"
    )
    fp1 = conversation_sources_fingerprint(tmp_path, [])
    path.write_text(path.read_text() + json.dumps({"role": "user", "message": {"content": [{"type": "text", "text": "More"}]}}) + "\n")
    fp2 = conversation_sources_fingerprint(tmp_path, [])
    assert fp1 != fp2
