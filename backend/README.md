# Autoresearch Backend

Real-time web UI and run orchestration API for autoresearch agent runs. Watches iteration TSV logs and `experiment:` git commits in any target project, and can spawn autoresearch runs via the web interface.

## Requirements

- [Conda](https://docs.conda.io/en/latest/miniconda.html) (Miniconda or Anaconda) — **recommended**
- Node.js 18+ (to build the frontend once)

## Quick start

From the autoresearch repo (or any checkout):

```bash
# Create/update the conda environment (one-time)
./backend/scripts/setup-env.sh
conda activate autoresearch-dashboard

# Build the web UI (first time only)
cd frontend && npm install && npm run build && cd ..

# Start the web app watching your project
./bin/autoresearch-dashboard --project /path/to/your/project
```

Open **http://127.0.0.1:3847** in your browser.

`./bin/autoresearch-dashboard` automatically uses the `autoresearch-dashboard` conda env when it exists, even if you forgot to activate it.

## Docker (local and cloud)

Build and run from the **autoresearch repo root** so the image can watch the workspace (including `tasks/*` projects):

```bash
docker compose up --build
```

Open **http://127.0.0.1:3847**. The compose file mounts the repo at `/workspace` inside the container (read-only). Set `DASHBOARD_WORKSPACE` in `.env` if you want to watch a different host directory.

### Plain `docker run`

```bash
docker build -f backend/Dockerfile -t autoresearch-dashboard .
docker run --rm -p 3847:3847 \
  -v "$(pwd):/workspace:ro" \
  -e DASHBOARD_PROJECT=/workspace \
  autoresearch-dashboard
```

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DASHBOARD_PROJECT` | `/workspace` | Directory watched for TSV logs and `.autoresearch/` |
| `DASHBOARD_HOST` | `0.0.0.0` | Bind address (use `0.0.0.0` in containers) |
| `DASHBOARD_PORT` | `3847` | HTTP port inside the container |

Optional CLI args are passed through the entrypoint, e.g. `--transcripts-dir /transcripts` when you mount transcripts. Docker Compose sets `CURSOR_TRANSCRIPTS_DIR` in `.env` so the **Conversation** tab streams Cursor agent transcripts in near real time (~2s).

### Cloud deployment notes

- Expose port `3847` (or map host port via `DASHBOARD_PORT`).
- Mount a persistent volume at `/workspace` containing agent run logs (or sync logs into that path).
- The image includes a `GET /api/health` health check for load balancers.
- For Kubernetes, set `livenessProbe` / `readinessProbe` on `/api/health`.
- Git timeline requires `.git` inside the mounted workspace; install is already in the image.

While `/autoresearch` (or any subcommand) runs in that project, the dashboard updates automatically when TSV rows are appended. If you start the dashboard at a workspace root that contains `tasks/`, each immediate `tasks/*` directory is treated as a child project and its runs appear in the same dashboard.

### Live agent conversations

The **Conversation** tab polls Cursor transcript JSONL every ~2 seconds (plus filesystem events when available). Enable **Follow live** to auto-select the newest session and scroll as new turns arrive. Sources:

- Cursor: `~/.cursor/projects/{slug}/agent-transcripts/` (auto-detected locally; mount into Docker via `CURSOR_TRANSCRIPTS_DIR`)
- Project mirror: `.autoresearch/conversation.jsonl` under the workspace or any `tasks/*` project

## Conda environment

| File | Purpose |
|------|---------|
| [environment.yml](environment.yml) | Conda env definition (`autoresearch-dashboard`, Python 3.12) |
| [scripts/setup-env.sh](scripts/setup-env.sh) | `conda env create` / `conda env update` helper |

Manual conda commands:

```bash
conda env create -f backend/environment.yml    # first time
conda env update -f backend/environment.yml --prune   # after dependency changes
conda activate autoresearch-dashboard
```

### Pip fallback (no conda)

If you cannot use conda, install into any Python 3.11+ virtualenv:

```bash
python3.12 -m pip install -r backend/requirements.txt
PYTHONPATH=. python3.12 -m backend.app.main --project .
```

## Development mode

Run API and UI separately for hot reload:

```bash
conda activate autoresearch-dashboard

# Terminal 1 — API + file watcher
./bin/autoresearch-dashboard --project . --port 3847

# Terminal 2 — Vite dev server (proxies /api to :3847)
cd frontend && npm run dev
```

Open **http://127.0.0.1:5174**.

## CLI options

| Flag | Default | Description |
|------|---------|-------------|
| `--project PATH` | current directory | Target repo where the agent writes TSV logs |
| `--transcripts-dir PATH` | auto-detect Cursor | Agent conversation JSONL directory (repeatable) |
| `--port` | `3847` | HTTP port |
| `--host` | `127.0.0.1` | Bind address |
| `--static PATH` | `frontend/dist` | Built React assets |

## What it watches

| Command | Log file pattern |
|---------|------------------|
| `autoresearch` | `autoresearch-results.tsv` |
| `security` | `security/*/security-audit-results.tsv` |
| `debug` | `debug/*/debug-results.tsv` |
| `fix` | `fix/*/fix-results.tsv` |
| `scenario` | `scenario/*/scenario-results.tsv` |
| `predict` | `predict/*/predict-results.tsv` |
| `learn` | `learn/*/learn-results.tsv` |
| `reason` | `reason/*/reason-results.tsv` |
| `ship` | `ship/*/ship-log.tsv` |
| `probe` | `probe/*/constraints.tsv`, `probe/*/questions-asked.tsv` |

## Optional session metadata

If the agent writes `.autoresearch/session.json` at loop start, the dashboard shows Goal, Scope, Metric, and Verify in the header. See [results-logging.md](../.claude/skills/autoresearch/references/results-logging.md).

## API

### Dashboard (read-only monitoring)

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Server status and watched project |
| `GET /api/projects` | Watched project roots (`tasks/*` included even without runs) |
| `GET /api/runs` | Discovered log files and project list |
| `GET /api/runs/{id}` | Single run details with session and active status |
| `GET /api/runs/{id}/iterations` | Normalized iteration rows |
| `GET /api/runs/{id}/summary` | Aggregates (keeps, discards, stuck warning) |
| `GET /api/git/commits` | Recent `experiment:` commits |
| `GET /api/git/commits/{hash}/stat` | Diff stat for a commit |
| `GET /api/trace` | Live agent trace events from `.autoresearch/trace.jsonl` |
| `GET /api/analytics` | Aggregated trace, model cost/usage, score, user, and latency metrics |
| `GET /api/runs/{id}/trace` | Per-run agent trace |
| `GET /api/runs/{id}/gemma4-trace` | Per-run Gemma4 execution trace |
| `GET /api/runs/{id}/gemma3-trace` | Per-run Gemma3 execution trace |
| `GET /api/runs/{id}/analytics` | Per-run analytics |
| `GET /api/conversations` | Agent conversation sessions |
| `GET /api/conversations/{id}/turns` | Full conversation turns |
| `GET /api/runs/{id}/artifacts` | Trace markdown/JSONL artifacts |
| `GET /api/events` | SSE stream for live updates |

### Orchestrator (run management)

| Endpoint | Description |
|----------|-------------|
| `POST /api/orchestrator/configs` | Create a run configuration |
| `GET /api/orchestrator/configs` | List saved configurations |
| `GET /api/orchestrator/configs/{id}` | Get a configuration |
| `PUT /api/orchestrator/configs/{id}` | Update a configuration |
| `DELETE /api/orchestrator/configs/{id}` | Delete a configuration |
| `POST /api/orchestrator/configs/validate` | Dry-run a verify command |
| `POST /api/orchestrator/configs/{id}/start` | Start a run from a configuration |
| `GET /api/orchestrator/instances` | List run instances |
| `GET /api/orchestrator/instances/{id}` | Get a run instance |
| `POST /api/orchestrator/instances/{id}/stop` | Stop a running instance |
| `GET /api/orchestrator/instances/{id}/logs` | Get stdout/stderr logs |

## Tests

```bash
conda activate autoresearch-dashboard
PYTHONPATH=. pytest backend/tests/ -q
```

Or without activating:

```bash
conda run -n autoresearch-dashboard env PYTHONPATH=. pytest backend/tests/ -q
```
