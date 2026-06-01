# agent_core

Gemma 4 agent runner built on the OpenAI Agents SDK with dynamic skill discovery.

## What it does

`agent_core` runs an agent that can discover and invoke skills from the filesystem. Skills are markdown instruction sets (`SKILL.md` files) with optional executable scripts. The agent exposes nine function tools:

- `list_skills` — discover available skills
- `read_skill` — load a skill's instructions
- `run_skill_script` — execute a script from a skill's `scripts/` directory
- `exec_command` — run a shell command (dangerous tokens are blocked)
- `read_file` — read file contents with optional offset/limit
- `write_file` — write content to a file
- `edit_file` — targeted string replacement in a file
- `list_directory` — list files and directories
- `apply_patch` — apply a unified diff patch

The runner connects to a Gemma 4 API by default (configurable via environment variables) and persists sessions in SQLite. Every run is logged to a JSONL trace file for inspection.

## Quick start

Install dependencies:

```bash
pip install -r requirements.txt
```

Set your API key:

```bash
export GEMMA4_API_KEY="your-key"
```

Run a one-shot prompt:

```bash
python -m agent_core chat "What skills are available?"
```

Start an interactive REPL:

```bash
python -m agent_core chat -i
```

Start the web UI:

```bash
python -m agent_core serve --port 8766
```

## CLI commands

### chat

```bash
python -m agent_core chat <prompt> [--interactive] [--system PROMPT] [--verbose]
```

Run a single prompt or start a multi-turn REPL session. The `--verbose` flag prints tool traces to stderr.

### serve

```bash
python -m agent_core serve [--host 127.0.0.1] [--port 8766]
```

Start a FastAPI server with REST and SSE streaming endpoints:

- `GET /api/health` — health check
- `GET /api/tasks` — list available tasks
- `GET /api/skills` — list discovered skills (optionally filtered by `?task=`)
- `POST /api/chat` — synchronous chat
- `POST /api/chat/stream` — Server-Sent Events streaming
- `POST /api/reset` — clear a session

### logs

```bash
python -m agent_core logs [--trace PATH] [--session ID] [--tail N] [--raw-stream]
```

Pretty-print the JSONL trace log. By default streaming token deltas are collapsed into single events.

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMMA4_API_KEY` | — | **Required.** API key for the model endpoint |
| `GEMMA4_MODEL_ID` | `google/gemma-4-E2B-it` | Model identifier |
| `GEMMA4_BASE_URL` | `https://api-lm.tr-dev.work/v1` | API base URL |

Skill discovery roots (searched for `SKILL.md` files):

- `.agents/skills/`
- `.claude/skills/`

## Package layout

| File | Purpose |
|------|---------|
| `runner.py` | `SkillAgentRunner`, `Gemma4AgentRunner`, `AgentResult` — core agent setup, streaming, and session management |
| `registry.py` | `SkillRegistry` — scan filesystem for skills, read SKILL.md, invoke scripts |
| `tools.py` | OpenAI Agents SDK `@function_tool` wrappers around the registry and filesystem operations |
| `server.py` | FastAPI app with REST and SSE endpoints |
| `mcp_server.py` | Optional stdio MCP server exposing the same skill tools |
| `logger.py` | `AgentLogger` — structured JSONL logging to file and stderr |
| `log_format.py` | Human-readable formatting and trace loading utilities |
| `metrics.py` | Token usage and latency tracking |
| `paths.py` | Shared paths for trace logs, session DB, and skill roots |
| `system_prompt.md` | Default system prompt loaded at runtime |
| `web/` | Static chat UI assets served by FastAPI |

## Trace log

Runs are recorded to `logs/agent-core/agent_core_trace.jsonl`. Each line is a JSON event with:

```json
{
  "ts": "2026-05-27T12:00:00+00:00",
  "session_id": "cli",
  "phase": "tool_call",
  "data": { "name": "list_skills", "arguments": "{}" }
}
```

Phases include: `user_request`, `model_request`, `model_delta`, `tool_call`, `tool_result`, `assistant_message`, `run_complete`, `metrics`, `error`.

## Skill format

A skill is a directory containing at minimum a `SKILL.md` with YAML frontmatter:

```markdown
---
name: my-skill
description: What this skill does
---

# Instructions

Tell the agent how to use this skill...
```

Optional `scripts/` directory contains executable helpers the agent can invoke via `run_skill_script`.

Skills can also be defined as flat `.md` files directly in a skill root (e.g., `.claude/skills/my-skill.md`).
