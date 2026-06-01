# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Autoresearch is a multi-agent platform that turns AI coding assistants into autonomous improvement engines. It provides:

- **Agent skills** (`claude-plugin/`, `plugins/`) — 11 subcommands (plan, debug, fix, security, ship, scenario, predict, learn, reason, probe, and the core autoresearch loop) distributed as plugins for Claude Code, OpenCode, and OpenAI Codex.
- **Dashboard** (`backend/` + `frontend/`) — A real-time FastAPI + React web UI that watches agent run logs, git commits, and conversation transcripts across any target project.
- **Orchestrator** — Can spawn autoresearch runs via the web UI, including a Cursor SDK runner that drives local Cursor agents programmatically.

The central research question is whether optimized agentic skills can help small models (tested on Gemma 3) approach the performance of state-of-the-art models.

## Common Commands

### Environment Setup

The backend requires Python 3.12 and prefers conda:

```bash
./backend/scripts/setup-env.sh          # Creates/updates conda env
conda activate autoresearch-dashboard
```

### Backend

```bash
# Run the dashboard server (watches current directory by default)
./bin/autoresearch-dashboard --project /path/to/target/project

# Run with dev API only (no static UI)
./bin/autoresearch-dashboard --project . --port 3847

# Run via Python directly
PYTHONPATH=. python -m backend.app.main --project .

# Run backend tests
PYTHONPATH=. pytest backend/tests/ -q

# Run all tests (includes codex plugin tests)
PYTHONPATH=. pytest backend/tests/ tests/ -q
```

### Frontend

```bash
cd frontend
npm install
npm run build         # Production build → dist/
npm run dev           # Vite dev server on :5174 (proxies /api to :3847)
```

### Docker

```bash
# Local full stack
cp .env.example .env    # Set CURSOR_API_KEY if using runner=cursor
docker compose up --build
```

### Cursor SDK Runner

```bash
export CURSOR_API_KEY="cursor_..."
./bin/autoresearch-cursor \
  --project tasks/gemma3-math-skill-optimization \
  --goal "Improve Gemma 3 math benchmark score" \
  --scope "skills/**" \
  --metric "accuracy (higher is better)" \
  --verify "./tests/verify-metric.sh" \
  --iterations 5
```

## Architecture

### Backend (`backend/app/`)

**Entry point:** `backend/app/main.py` creates a FastAPI app, wires up `DashboardState` + `EventBus` + `RunManager`, and starts filesystem watchers.

**Key modules:**

- `core/state.py` — `DashboardState` is the central in-memory state. It discovers runs, projects, git commits, conversations, trace events, and experiments. It publishes SSE events when data changes. Thread-safe with locking.
- `core/discovery.py` — Scans the watched project for autoresearch TSV logs (`autoresearch-results.tsv`, `security-audit-results.tsv`, etc.) and builds `RunInfo` / `ProjectInfo` objects. Treats immediate `tasks/*` subdirectories as child projects.
- `core/watcher.py` — Uses `watchdog` to monitor TSV logs, trace JSONL, experiments, and transcripts. Falls back to periodic polling.
- `core/parsers.py` — Parses TSV iteration logs into normalized rows and computes summaries (keeps, discards, stuck warnings).
- `core/git_ops.py` — Lists `experiment:` prefixed commits and computes diff stats.
- `core/conversations.py` — Discovers Cursor agent transcripts from `~/.cursor/projects/.../agent-transcripts/` and project-local `.autoresearch/conversation.jsonl`.
- `core/trace.py` — Parses `.autoresearch/trace.jsonl`, `gemma3_trace.jsonl`, and `gemma4_trace.jsonl` into analytics.
- `api/routes.py` — FastAPI routers grouped by domain (health, projects, runs, conversations, git, skills, events, orchestrator).
- `api/events.py` — `EventBus` decouples filesystem watchers from SSE streaming.
- `orchestrator/manager.py` — `RunManager` handles run configs → spawn → monitor → stop. Supports subprocess runners and Cursor SDK runner.
- `orchestrator/cursor_runner.py` — Drives Cursor SDK agents locally.
- `orchestrator/models.py` — Pydantic models for `RunConfig` and `RunInstance`.
- `orchestrator/store.py` — Simple JSON file store for orchestrator state.

**Important:** The backend is designed to watch an *external* project directory (via `--project`), not just itself. It reads TSV logs and git history from that target project.

### Frontend (`frontend/src/`)

**Stack:** React 18, TypeScript, Vite, React Router (HashRouter), Lucide React. No Tailwind or shadcn in this repo — styling is plain CSS (`index.css`).

**Structure:**

- `App.tsx` — Routes: `/` (Dashboard), `/runs` (RunManager), `/runs/new` (RunConfigurator)
- `pages/Dashboard.tsx` — Main observability page with iteration table, metric chart, git timeline, trace viewers, conversation tab
- `pages/RunConfigurator.tsx` — Create/edit run configs for the orchestrator
- `pages/RunManager.tsx` — List and control run instances
- `hooks/useDashboard.ts` — Central data fetching and SSE event handling
- `hooks/useRuns.ts` — Orchestrator run instance state
- `components/IterationTable.tsx`, `MetricChart.tsx`, `GitTimeline.tsx`, `ConversationView.tsx`, `AgentTrace.tsx`, `ExperimentsView.tsx`, `Analytics.tsx`, `SkillsView.tsx`

The Vite dev server proxies `/api` to `http://127.0.0.1:3847`.

### Plugin Distribution

- `claude-plugin/` — Skills and commands for Claude Code. `claude-plugin/skills/autoresearch/SKILL.md` is the main skill router; `references/*.md` contain per-command workflows.
- `plugins/autoresearch/` — Codex plugin package. `plugins/autoresearch/scripts/autoresearch_cli.py` is the wrapper CLI. `plugins/autoresearch/skills/autoresearch/SKILL.md` mirrors the Claude skill.
- `bin/autoresearch` — Convenience wrapper for the Codex CLI.
- `bin/autoresearch-dashboard` — Entry point for the dashboard server; auto-detects conda env.
- `bin/autoresearch-cursor` — Entry point for the Cursor SDK runner.

### Autoresearch Loop Protocol

The core loop is: **Modify → Verify → Keep/Discard → Repeat**.

Key files the agent reads/writes in the *target* project (not this repo):

- `autoresearch-results.tsv` — Iteration log with columns: iteration, commit, metric, delta, status, description
- `.autoresearch/session.json` — Goal, scope, metric, verify command (displayed in dashboard header)
- `.autoresearch/trace.jsonl` — Agent execution trace
- `.autoresearch/experiment.jsonl` — Experiment metadata
- `.autoresearch/conversation.jsonl` — Mirror of agent conversation
- Git commits prefixed with `experiment:` — Atomic changes, auto-reverted on failure

### Design System

`DESIGN.md` defines the Langfuse-inspired design system (colors, typography, components). This is primarily documentation — the frontend uses plain CSS, not Tailwind. Dark mode is supported via CSS variables and a theme toggle.

## Development Notes

- `PYTHONPATH=.` is required when running Python directly from the repo root because imports use absolute `backend.app.*` and `backend.scripts.*` paths.
- The dashboard server defaults to port `3847`. The Vite dev server defaults to `5174`.
- The orchestrator stores run configs and instances in JSON files under the watched project's `.autoresearch/` directory.
- Cursor SDK integration requires `CURSOR_API_KEY` in `.env` or environment. The Docker Compose setup mounts `~/.cursor/projects/.../agent-transcripts` for live conversation streaming.
- To run a single backend test file: `PYTHONPATH=. pytest backend/tests/test_parsers.py -q`
- To run a single test: `PYTHONPATH=. pytest backend/tests/test_parsers.py::TestParseLogFile::test_name -q`
