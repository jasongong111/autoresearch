"""Optional stdio MCP server exposing the same skill tools as function tools."""

from __future__ import annotations

import json
import sys

from .paths import default_skill_roots
from .registry import SkillRegistry

REGISTRY = SkillRegistry(*default_skill_roots())

TOOLS = [
    {
        "name": "list_skills",
        "description": "List available agent skills with names, descriptions, and script filenames.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "read_skill",
        "description": "Read the SKILL.md instructions for a skill by name.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "skill_name": {
                    "type": "string",
                    "description": "Skill name from list_skills, e.g. gemma3-delegate",
                }
            },
            "required": ["skill_name"],
        },
    },
    {
        "name": "run_skill_script",
        "description": (
            "Run an executable script from a skill's scripts/ directory. "
            "Read the skill first to learn the script contract."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "skill_name": {"type": "string"},
                "script_name": {"type": "string"},
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "CLI arguments passed to the script",
                },
            },
            "required": ["skill_name", "script_name"],
        },
    },
]


def _dispatch_tool(name: str, arguments: dict) -> str:
    if name == "list_skills":
        return REGISTRY.list_skills()
    if name == "read_skill":
        return REGISTRY.read_skill(str(arguments["skill_name"]))
    if name == "run_skill_script":
        args = arguments.get("args")
        script_args = list(args) if isinstance(args, list) else None
        return REGISTRY.run_skill_script(
            str(arguments["skill_name"]),
            str(arguments["script_name"]),
            script_args,
        )
    raise ValueError(f"Unknown tool: {name}")


def _send(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()


def _handle_request(request: dict) -> None:
    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params") or {}

    if method == "initialize":
        _send(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "autoresearch-skills", "version": "1.0.0"},
                },
            }
        )
        return

    if method == "notifications/initialized":
        return

    if method == "tools/list":
        _send(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": TOOLS},
            }
        )
        return

    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments") or {}
        try:
            content = _dispatch_tool(tool_name, arguments)
            _send(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"content": [{"type": "text", "text": content}]},
                }
            )
        except Exception as exc:  # noqa: BLE001
            _send(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error: {exc}"}],
                        "isError": True,
                    },
                }
            )
        return

    if request_id is not None:
        _send(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }
        )


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(request, dict):
            _handle_request(request)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
