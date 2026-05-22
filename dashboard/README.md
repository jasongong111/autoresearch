# Autoresearch Dashboard

Real-time web UI for monitoring autoresearch agent runs. Watches iteration TSV logs and `experiment:` git commits in any target project.

## Requirements

- [Conda](https://docs.conda.io/en/latest/miniconda.html) (Miniconda or Anaconda) — **recommended**
- Node.js 18+ (to build the UI once)

## Quick start

From the autoresearch repo (or any checkout):

```bash
# Create/update the conda environment (one-time)
./dashboard/scripts/setup-env.sh
conda activate autoresearch-dashboard

# Build the web UI (first time only)
cd dashboard/web && npm install && npm run build && cd ../..

# Start the dashboard watching your project
./bin/autoresearch-dashboard --project /path/to/your/project
```

Open **http://127.0.0.1:3847** in your browser.

`./bin/autoresearch-dashboard` automatically uses the `autoresearch-dashboard` conda env when it exists, even if you forgot to activate it.

While `/autoresearch` (or any subcommand) runs in that project, the dashboard updates automatically when TSV rows are appended.

## Conda environment

| File | Purpose |
|------|---------|
| [environment.yml](environment.yml) | Conda env definition (`autoresearch-dashboard`, Python 3.12) |
| [scripts/setup-env.sh](scripts/setup-env.sh) | `conda env create` / `conda env update` helper |

Manual conda commands:

```bash
conda env create -f dashboard/environment.yml    # first time
conda env update -f dashboard/environment.yml --prune   # after dependency changes
conda activate autoresearch-dashboard
```

### Pip fallback (no conda)

If you cannot use conda, install into any Python 3.11+ virtualenv:

```bash
python3.12 -m pip install -r dashboard/requirements.txt
PYTHONPATH=. python3.12 -m dashboard.server.main --project .
```

## Development mode

Run API and UI separately for hot reload:

```bash
conda activate autoresearch-dashboard

# Terminal 1 — API + file watcher
./bin/autoresearch-dashboard --project . --port 3847

# Terminal 2 — Vite dev server (proxies /api to :3847)
cd dashboard/web && npm run dev
```

Open **http://127.0.0.1:5174**.

## CLI options

| Flag | Default | Description |
|------|---------|-------------|
| `--project PATH` | current directory | Target repo where the agent writes TSV logs |
| `--port` | `3847` | HTTP port |
| `--host` | `127.0.0.1` | Bind address |
| `--static PATH` | `dashboard/web/dist` | Built React assets |

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

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Server status and watched project |
| `GET /api/runs` | Discovered log files |
| `GET /api/runs/{id}/iterations` | Normalized iteration rows |
| `GET /api/runs/{id}/summary` | Aggregates (keeps, discards, stuck warning) |
| `GET /api/git/commits` | Recent `experiment:` commits |
| `GET /api/trace` | Live agent trace events from `.autoresearch/trace.jsonl` |
| `GET /api/runs/{id}/artifacts` | Trace markdown/JSONL files in the run directory |
| `GET /api/events` | SSE stream (`run_updated`, `git_updated`, `trace_updated`) |

## Tests

```bash
conda activate autoresearch-dashboard
PYTHONPATH=. pytest dashboard/tests/ -q
```

Or without activating:

```bash
conda run -n autoresearch-dashboard env PYTHONPATH=. pytest dashboard/tests/ -q
```
