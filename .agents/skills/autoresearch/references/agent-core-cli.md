# Agent Core CLI

This document explains how to run the `agent_core` agent from the command line. The agent is a Gemma 4-powered skill agent built on the OpenAI Agents SDK that discovers and invokes skills from the filesystem.

**Prerequisite:** Set `GEMMA4_API_KEY` in your environment before running any command.

---

## 1. Quick Start

```bash
export GEMMA4_API_KEY="your-key-here"

# One-shot prompt
python -m agent_core chat "What skills are available?"

# Interactive REPL
python -m agent_core chat -i

# Start web UI server
python -m agent_core serve --port 8766
```

---

## 2. CLI Entry Points

There are three ways to invoke the agent:

### 2.1 Python module (recommended for development)

```bash
python -m agent_core <command> [options]
```

Requires `PYTHONPATH=.` when run from the repo root, or use the wrapper script below.

### 2.2 Wrapper script

```bash
./bin/agent-core <command> [options]
```

This script automatically:
- Sets `PYTHONPATH` to the repo root
- Prefers the `autoresearch-dashboard` conda environment if available
- Falls back to system Python (3.12, 3.11, or 3)

### 2.3 Docker

```bash
docker build -f agent_core/Dockerfile -t agent-core .
docker run --rm -p 8766:8766 -e GEMMA4_API_KEY="..." agent-core
```

The Docker image runs `serve` by default on `0.0.0.0:8766`.

---

## 3. Commands

### 3.1 chat

Run a one-shot prompt or start an interactive REPL session.

```bash
python -m agent_core chat <prompt> [--interactive] [--system PROMPT] [--verbose]
```

| Option | Description |
|---|---|
| `prompt` | Positional argument for a one-shot user message |
| `--interactive`, `-i` | Start a multi-turn REPL session (type `exit` or Ctrl-D to quit) |
| `--system` | Override the base system prompt (skill catalog is still appended) |
| `--verbose`, `-v` | Print tool traces to stderr |

Examples:

```bash
# One-shot
python -m agent_core chat "List available skills"

# Interactive REPL
python -m agent_core chat -i

# Custom system prompt with verbose tool tracing
python -m agent_core chat "Refactor this function" --system "You are a senior Go engineer" --verbose
```

### 3.2 serve

Start the FastAPI web server with REST and SSE endpoints.

```bash
python -m agent_core serve [--host 127.0.0.1] [--port 8766]
```

| Option | Default | Description |
|---|---|---|
| `--host` | `127.0.0.1` | Bind address |
| `--port` | `8766` | Listen port |

Endpoints:

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/tasks` | List available tasks |
| `GET` | `/api/skills?task=` | List discovered skills (optionally filtered by task) |
| `POST` | `/api/chat` | Synchronous chat |
| `POST` | `/api/chat/stream` | Server-Sent Events streaming |
| `POST` | `/api/reset` | Clear a session |
| `GET` | `/` | Static chat UI |

Example:

```bash
python -m agent_core serve --host 0.0.0.0 --port 8766
```

### 3.3 logs

Pretty-print the JSONL agent trace log.

```bash
python -m agent_core logs [--trace PATH] [--session ID] [--tail N] [--raw-stream]
```

| Option | Default | Description |
|---|---|---|
| `--trace` | `logs/agent-core/agent_core_trace.jsonl` | Path to trace JSONL file |
| `--session` | — | Filter to a specific session ID |
| `--tail` | `0` (all) | Only show the last N events |
| `--raw-stream` | false | Do not collapse streaming token deltas |

Examples:

```bash
# Show all trace events
python -m agent_core logs

# Tail last 50 events
python -m agent_core logs --tail 50

# Show only the current CLI session
python -m agent_core logs --session cli

# Show raw streaming deltas
python -m agent_core logs --tail 100 --raw-stream
```

---

## 4. Configuration

### Environment Variables

| Variable | Default | Required | Description |
|---|---|---|---|
| `GEMMA4_API_KEY` | — | **Yes** | API key for the model endpoint |
| `GEMMA4_MODEL_ID` | `google/gemma-4-E2B-it` | No | Model identifier |
| `GEMMA4_BASE_URL` | `https://api-lm.tr-dev.work/v1` | No | API base URL |

These are read from the environment and from `.env` in the repo root.

### Skill Discovery Roots

**Without a task** — searches repo plugin skills:

- `.agents/skills/`
- `.claude/skills/`

**With `task=<name>`** (CLI `--task`, API `task` field, or harness `run(..., task="...")`) — loads **only**:

- `tasks/<name>/skills/`

This prevents autoresearch benchmarks from accidentally reading `.claude/skills/<same-name>/` instead of the task copy under optimization.

Verify binding:

```bash
curl -s 'http://127.0.0.1:8766/api/skills?task=simple-lookups' | jq '.skill_roots, .skills[].path'
# skill_roots should be only tasks/simple-lookups/skills
```

CLI:

```bash
python -m agent_core chat "What is in stock?" --task simple-lookups
```

---

## 5. Programmatic Usage

You can also run the agent from Python:

```python
from agent_core.runner import SkillAgentRunner

runner = SkillAgentRunner(verbose=True)
result = runner.run("What skills are available?")
print(result.answer)
runner.close()
```

For streaming:

```python
import asyncio

async def stream_chat():
    runner = SkillAgentRunner()
    async for event in runner.run_stream("Hello", session_id="demo"):
        print(event)
    runner.close()

asyncio.run(stream_chat())
```

---

## 6. MCP Server

An optional stdio MCP server is available:

```bash
python -m agent_core.mcp_server
```

This exposes `list_skills`, `read_skill`, and `run_skill_script` via JSON-RPC 2.0 for integration with MCP-compatible clients.

---

## 7. Skill Verification in Autoresearch

When autoresearch optimizes a skill for the gemma-4-e2b model, the Verify command loads `expected/eval.json`, runs each test case through `agent_core`, rates gemma4's output against the expectations, and prints a single metric number.

### How it works

1. The verify script reads `expected/eval.json` — an array of test cases with `id`, `name`, `prompt`, and `expectations`.
2. For each test case, it calls `agent_core` with the `--task` flag so the runner discovers skills from `tasks/<task-name>/skills/`.
3. The agent runs the prompt through the gemma-4-e2b model using the current skill instructions.
4. The scorer rates gemma4's output against each item in the `expectations` array.
5. The script aggregates the scores and prints a single metric number to stdout.
6. The autoresearch optimizer observes the metric and decides keep/discard.

### Example eval.json

```json
[
  {
    "id": 1,
    "name": "employee-lookup-by-code",
    "prompt": "Find the full details for employee E-0004...",
    "expectations": [
      "The agent does not use SQL, psql, asyncpg, or any direct database connection",
      "The agent queries the HTTP API at localhost:8000/api/v1",
      "The output includes the employee's name, role, salary_usd, and phone"
    ]
  }
]
```

### Example verify script pattern

```bash
#!/bin/bash
# verify.sh
set -e
export GEMMA4_API_KEY="${GEMMA4_API_KEY:?missing}"

# Run the eval via agent_core and score against expectations
python .claude/skills/autoresearch/scripts/run_eval.py \
  --eval expected/eval.json \
  --task "$(basename "$PWD")" \
  --metric pass-rate
```

For custom scoring, wrap `run_eval.py` or use the `SkillAgentRunner` API directly:

```python
from agent_core.runner import SkillAgentRunner
import json

runner = SkillAgentRunner()
with open("expected/eval.json") as f:
    cases = json.load(f)

total = 0
passed = 0
for case in cases:
    result = runner.run(case["prompt"], task="simple-lookups")
    score = rate_output(result.answer, case["expectations"])
    total += len(case["expectations"])
    passed += score

print(passed / total)  # metric: fraction of expectations met
runner.close()
```

### Trace inspection

After a verify run, inspect the agent run trace to understand model failures:

```bash
# Pretty-print the last 50 trace events
python -m agent_core logs --trace logs/agent-core/agent_core_trace.jsonl --tail 50
```

The trace shows tool calls, reasoning, and final answers — use it to diagnose why a skill change improved or regressed the metric.
