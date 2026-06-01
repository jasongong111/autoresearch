# AGENTS.md — Autoresearch

> Drop this file into your project root. Any AI agent (Claude Code, Codex, OpenCode, Gemini CLI, etc.) can then use Autoresearch immediately.

## What is Autoresearch?

Autonomous goal-directed iteration based on [Karpathy's autoresearch](https://github.com/karpathy/autoresearch). One metric, constrained scope, fast verification, automatic rollback, git as memory. Works on ANY domain — code, content, marketing, sales, DevOps — anything with a measurable metric.

**Core loop:** Modify → Verify → Keep/Discard → Repeat.

---

## Project Research Question

This project investigates whether optimized agentic skills can help a small language model approach the performance of state-of-the-art models on complex agentic tasks.

Use Gemma 4 as the testbed. The central research question is:

> Can optimized agentic skills help models approach the performance of state-of-the-art models?

The experimental comparison should preserve three distinct conditions:

1. **Gemma 4 without skill support** — baseline performance.
2. **Gemma 4 with a frontier-generated skill** — measures initial skill transfer.
3. **Gemma 4 with an optimized skill** — measures the additional gain from iterative skill refinement.

The autoresearch agent is an external observer and optimizer, not the model under evaluation. It may inspect results, traces, metrics, and failures, then modify the skill. It should not change the benchmark, evaluator, scoring pipeline, or Gemma 4 model configuration unless the user explicitly asks.

For this research track, interpret the loop as:

```text
Modify skill -> Run Gemma 4 -> Score result -> Keep/Discard -> Repeat
```

Keep the editable target restricted to the skill. Keep verification mechanical, numeric, and reproducible. Treat `.autoresearch/gemma4-trace.jsonl` as the subject-model (Gemma 4) execution trace, and `.autoresearch/trace.jsonl` as the autoresearch observer/optimizer trace.

Within the Modify step, "the skill" means the complete agent skill package: `SKILL.md`, deterministic scripts or CLIs the agent can run, reference documentation such as domain rules and FAQs, and reusable assets such as code templates, boilerplate files, and configurations.

---

## Task Folder Workspace

Research and skill-optimization loops run **inside a task folder** under `tasks/<task-name>/`, not at the autoresearch repo root. Each task folder is its own git repo and project root: Verify runs with `cwd` set to that directory, and the dashboard watches it as a child project when the workspace contains `tasks/`.

**Example:** [`tasks/gemma4-math-skill-optimization/`](tasks/gemma4-math-skill-optimization/)

Before starting the loop:

1. `cd` into the task folder (or point the orchestrator `--project` path there).
2. **Initialize git if missing** — autoresearch requires git for `experiment:` commits and rollbacks.
3. Read the task `README.md` for Goal, Scope, Verify, and task-specific rules.
4. Run Verify from the task root (e.g. `./tests/verify-metric.sh`).

```bash
cd tasks/<task-name>
git rev-parse --git-dir || { git init && git add . && git commit -m "baseline: initial task state"; }
```

### Task folder layout

```
tasks/<task-name>/
├── README.md                 # Goal, verify command, editable scope, run instructions
├── input.md                  # Optional: instructions merged with each benchmark prompt
├── skills/                   # EDITABLE — optimizer target (skill package)
│   └── <skill-name>/
│       ├── SKILL.md
│       ├── references/       # Optional: deep docs, FAQs, examples
│       ├── scripts/          # Optional: deterministic CLIs
│       └── assets/           # Optional: templates, configs, boilerplate
├── expected/                 # READ-ONLY — dev/golden set visible during optimization
├── holdout/                  # READ-ONLY — hidden eval set (do not read while optimizing)
├── tests/                    # READ-ONLY — benchmark harness and verify script
├── autoresearch-results.tsv  # Generated — iteration log
└── .autoresearch/            # Generated — runtime traces and session metadata
    ├── session.json          # Goal, Scope, Metric, Verify for the dashboard
    ├── trace.jsonl           # Autoresearch observer/optimizer trace
    └── gemma4-trace.jsonl    # Subject-model execution trace (name varies by task)
```

### Edit boundaries

| Area | Role | Optimizer may edit? |
|------|------|---------------------|
| `skills/**` | Agent skill package under test | **Yes** — only in-scope Modify target |
| `tests/**` | Evaluator, scorer, verify script | **No** |
| `expected/**` | Dev benchmark set | **No** |
| `holdout/**` | Hidden final benchmark | **No** — do not read during the loop |
| `input.md` | Shared prompt prefix | **No** |
| `.autoresearch/**` | Traces and session files | **No** — write-only metadata from runs |

After optimization, run holdout evaluation separately — never tune against holdout during the loop.

---

## Installation

### Claude Code (plugin)

```
/plugin marketplace add uditgoenka/autoresearch
/plugin install autoresearch@autoresearch
```

Restart session after install. All 11 commands become available as `/autoresearch` and `/autoresearch:<subcommand>`.

### Codex (plugin)

```bash
git clone https://github.com/uditgoenka/autoresearch.git
cd autoresearch
python3 plugins/autoresearch/scripts/install_local_plugin.py
```

Use the wrapper CLI: `bin/autoresearch <subcommand> [flags]`

### Manual (any agent)

Copy the skill files into your agent's skill directory:

```bash
git clone https://github.com/uditgoenka/autoresearch.git

# Claude Code
cp -r autoresearch/claude-plugin/skills/autoresearch .claude/skills/autoresearch
cp -r autoresearch/claude-plugin/commands/autoresearch .claude/commands/autoresearch
cp autoresearch/claude-plugin/commands/autoresearch.md .claude/commands/autoresearch.md

# Codex
cp -r autoresearch/plugins/autoresearch ~/.agents/plugins/autoresearch

# Cursor (this repo)
# Skills already live at .agents/skills/autoresearch/ when cloned
```

---

## Commands

| Command | Purpose |
|---------|---------|
| `autoresearch` | Autonomous iteration loop (unlimited or bounded with `Iterations: N`) |
| `autoresearch:plan` | Interactive wizard: Goal → Scope, Metric, Direction, Verify config |
| `autoresearch:debug` | Autonomous bug-hunting — scientific method + iterative investigation |
| `autoresearch:fix` | Autonomous error repair — one fix per iteration until zero errors |
| `autoresearch:security` | STRIDE + OWASP + red-team security audit (read-only unless `--fix`) |
| `autoresearch:ship` | Universal shipping workflow — 8 phases, 9 shipment types |
| `autoresearch:scenario` | Scenario exploration — 12 dimensions, edge cases, derivative scenarios |
| `autoresearch:predict` | Multi-persona swarm — 5 expert perspectives before acting |
| `autoresearch:learn` | Autonomous documentation engine — scout, generate, validate, fix |
| `autoresearch:reason` | Adversarial refinement — blind judge panel for subjective domains |
| `autoresearch:probe` | Adversarial requirement / assumption interrogation — 8 personas probe to mechanical saturation, emits ready-to-run autoresearch config |

---

## Dashboard (real-time monitoring)

Watch iteration logs and git experiments in a local web UI while any autoresearch command runs:

```bash
./backend/scripts/setup-env.sh
conda activate autoresearch-dashboard
cd frontend && npm install && npm run build && cd ..
./bin/autoresearch-dashboard --project /path/to/target/repo
```

Open http://127.0.0.1:3847. See [backend/README.md](backend/README.md) for dev mode, API, and supported log formats.

When the dashboard watches a workspace root that contains `tasks/`, each immediate `tasks/*` directory appears as a child project with its own runs, git history, and traces.

### Orchestrator and Cursor SDK runner

The dashboard can spawn autoresearch runs from the web UI. For programmatic runs with the Cursor SDK:

```bash
export CURSOR_API_KEY="cursor_..."
./bin/autoresearch-cursor \
  --project tasks/gemma4-math-skill-optimization \
  --goal "Improve Gemma 4 math benchmark score" \
  --scope "skills/**" \
  --metric "accuracy (higher is better)" \
  --verify "./tests/verify-metric.sh" \
  --iterations 5
```

Set `CURSOR_API_KEY` in `.env` (see `.env.example`). Docker Compose runs the full stack with `docker compose up --build`.

---

## Sample project (research task)

The Gemma 4 math skill optimization task lives at [`tasks/gemma4-math-skill-optimization/`](tasks/gemma4-math-skill-optimization/). Initialize git there, set `GEMMA4_API_KEY`, then run `/autoresearch` with `Verify: ./tests/verify-metric.sh` (see task README).

### Research-track quick start

```
cd tasks/gemma4-math-skill-optimization
/autoresearch
Goal: Maximize Gemma 4 accuracy on the dev math benchmark
Scope: skills/**/*
Metric: accuracy % (higher is better)
Direction: higher
Verify: ./tests/verify-metric.sh
Iterations: 20
```

---

## Quick Start

### Basic autonomous loop

```
autoresearch
Goal: Increase test coverage from 72% to 90%
Scope: src/**/*.test.ts, src/**/*.ts
Metric: coverage % (higher is better)
Verify: npm test -- --coverage | grep "All files"
Iterations: 50
```

### Don't know what metric to use?

```
autoresearch:plan
Goal: Make the API respond faster
```

The wizard walks you through scope, metric, direction, and verify — with dry-run validation.

### Hunt all bugs

```
autoresearch:debug
Scope: src/api/**/*.ts
Symptom: API returns 500 on POST /users
Iterations: 20
```

### Fix all errors

```
autoresearch:fix
```

Auto-detects broken tests/types/lint/build, fixes one at a time, stops at zero errors.

### Security audit

```
autoresearch:security
Scope: src/**/*.ts
Iterations: 10
```

### Ship a PR

```
autoresearch:ship --auto
```

### Explore edge cases

```
autoresearch:scenario
Scenario: User attempts checkout with expired card
Iterations: 25
```

### Get expert opinions before acting

```
autoresearch:predict --chain debug
Scope: src/auth/**/*.ts
```

### Refine a subjective decision

```
autoresearch:reason
Task: Should we use event sourcing for order management?
Domain: software
Iterations: 8
```

---

## Configuration Fields

| Field | Required | Description |
|-------|----------|-------------|
| `Goal` | Yes | What you want to achieve (plain language) |
| `Scope` | Yes | Glob patterns for files the agent can modify |
| `Metric` | Yes | What number to optimize (higher/lower + unit) |
| `Verify` | Yes | Shell command that outputs the metric value |
| `Guard` | No | Safety command that must always pass (prevents regressions) |
| `Iterations` | No | Bounded run — stop after N iterations (default: unlimited) |
| `Direction` | No | `higher` or `lower` — which direction is better |

---

## Flags

### Core loop (`autoresearch`)

| Flag | Purpose |
|------|---------|
| `--scope <glob>` | Override scope |
| `--iterations <N>` | Bounded iteration count |

### Security (`autoresearch:security`)

| Flag | Purpose |
|------|---------|
| `--diff` | Only audit changed files |
| `--fix` | Auto-fix Critical/High findings |
| `--fail-on <severity>` | Non-zero exit for CI/CD gating |

### Ship (`autoresearch:ship`)

| Flag | Purpose |
|------|---------|
| `--auto` | Auto-approve if checklist passes |
| `--dry-run` | Validate without shipping |
| `--checklist-only` | Just check readiness |
| `--rollback` | Undo last ship |
| `--monitor <N>` | Post-ship monitoring (minutes) |

### Debug (`autoresearch:debug`)

| Flag | Purpose |
|------|---------|
| `--fix` | After hunting, auto-switch to fix mode |
| `--scope <glob>` | Limit investigation scope |
| `--symptom "<text>"` | Pre-fill symptom |

### Fix (`autoresearch:fix`)

| Flag | Purpose |
|------|---------|
| `--target <command>` | Explicit verify command |
| `--guard <command>` | Safety command |
| `--category <type>` | Only fix: test, type, lint, or build |
| `--from-debug` | Read findings from latest debug session |

### Predict (`autoresearch:predict`)

| Flag | Purpose |
|------|---------|
| `--chain <commands>` | Chain output to other commands |

### Reason (`autoresearch:reason`)

| Flag | Purpose |
|------|---------|
| `--iterations <N>` | Bounded rounds |
| `--judges <N>` | Judge count (3-7, odd preferred) |
| `--convergence <N>` | Consecutive wins to converge (default: 3) |
| `--mode <mode>` | convergent, creative, debate |
| `--domain <type>` | software, product, business, security, research, content |
| `--chain <targets>` | Chain converged output to other commands |

### Learn (`autoresearch:learn`)

| Flag | Purpose |
|------|---------|
| `--mode <mode>` | init, update, check, summarize |
| `--depth <level>` | shallow, standard, deep |
| `--file <path>` | Update single doc |

### Scenario (`autoresearch:scenario`)

| Flag | Purpose |
|------|---------|
| `--domain <type>` | software, product, business, security, marketing |
| `--depth <level>` | shallow, standard, deep |
| `--format <type>` | use-cases, user-stories, test-scenarios, threat-scenarios |
| `--focus <area>` | edge-cases, failures, security, scale |

---

## Chaining Commands

Commands can be chained with `--chain`:

```
autoresearch:debug --fix                      # debug → auto-fix
autoresearch:predict --chain debug            # predict → debug
autoresearch:predict --chain scenario,debug,fix  # full quality pipeline
autoresearch:reason --chain predict           # converge → stress-test
autoresearch:reason --chain plan,fix          # converge → implement
autoresearch:probe --chain plan,autoresearch  # interrogate → config → loop
autoresearch:probe --chain reason             # interrogate → debate → converge
```

---

## 8 Critical Rules

1. **Loop until done** — unbounded: forever. Bounded: N times then summarize.
2. **Read before write** — understand full context before modifying.
3. **One change per iteration** — atomic changes. If it breaks, you know why.
4. **Mechanical verification only** — no subjective "looks good." Use metrics.
5. **Automatic rollback** — failed changes revert instantly via `git revert`.
6. **Simplicity wins** — equal results + less code = KEEP.
7. **Git is memory** — experiments committed with `experiment:` prefix, agent reads `git log` + `git diff` before each iteration.
8. **When stuck, think harder** — re-read, combine near-misses, try radical changes.

---

## Results Tracking

Every iteration is logged in TSV format:

```tsv
iteration  commit   metric  delta   status    description
0          a1b2c3d  85.2    0.0     baseline  initial state
1          b2c3d4e  87.1    +1.9    keep      add tests for auth edge cases
2          -        86.5    -0.6    discard   refactor test helpers (broke 2 tests)
3          c3d4e5f  88.3    +1.2    keep      add error handling tests
```

---

## Agent-Specific Notes

### Claude Code

- Commands are invoked as `/autoresearch` and `/autoresearch:<subcommand>`
- Interactive setup uses `AskUserQuestion` when context is missing
- Skill files: `.claude/skills/autoresearch/SKILL.md` + `references/*.md`

### Codex

- Commands are invoked as plain text: `autoresearch` and `autoresearch:<subcommand>`
- Interactive setup uses `request_user_input` or direct question batches
- Plugin files: `plugins/autoresearch/` with `skills/`, `resources/`, `scripts/`
- Wrapper CLI: `bin/autoresearch <subcommand> [flags]`
- Canonical command spec: `plugins/autoresearch/resources/autoresearch-command-spec.json`

### Cursor and other agents (OpenCode, Gemini CLI, etc.)

- Skill files for this repo: `.agents/skills/autoresearch/SKILL.md` + `references/*.md`
- Model API skills: `.agents/skills/gemma3-api/SKILL.md`, `.agents/skills/gemma4-api/SKILL.md`
- Read this file for the command surface and configuration contract
- Use the core loop protocol: review → change → commit → verify → keep/revert → log
- Git is required in the **task folder** — the loop uses `git commit`, `git revert`, `git log`, `git diff`
- Each iteration must be atomic (one change, one commit, one verification)
- For detailed workflow references, see: `claude-plugin/skills/autoresearch/references/*.md` or `.agents/skills/autoresearch/references/*.md`

---

## Repository Structure

```
autoresearch/
├── AGENTS.md                          ← You are here
├── CLAUDE.md                          ← Claude Code repo guidance
├── README.md                          ← Full documentation
├── COMPARISON.md                      ← Karpathy's vs Claude Autoresearch
├── guide/                             ← Comprehensive guides per command
├── tasks/                             ← Research task folders (each is its own git repo)
│   └── gemma4-math-skill-optimization/
├── .agents/skills/                    ← Cursor agent skills (autoresearch, gemma4-api)
├── backend/                           ← Dashboard FastAPI server
├── frontend/                          ← Dashboard React UI
├── claude-plugin/                     ← Claude Code distribution package
│   ├── skills/autoresearch/SKILL.md   ← Main skill + references/
│   └── commands/autoresearch/         ← Subcommand registrations
├── plugins/autoresearch/              ← Codex distribution package
│   ├── skills/autoresearch/SKILL.md   ← Codex skill router + references/
│   ├── resources/                     ← Command spec JSON
│   └── scripts/                       ← Wrapper CLI
└── bin/
    ├── autoresearch                   ← Codex CLI wrapper
    ├── autoresearch-dashboard         ← Dashboard server
    └── autoresearch-cursor            ← Cursor SDK runner
```

---

## License

MIT — see [LICENSE](LICENSE).

## Credits

- [Andrej Karpathy](https://github.com/karpathy) — [autoresearch](https://github.com/karpathy/autoresearch)
- [Anthropic](https://anthropic.com) — Claude Code
- [OpenAI](https://openai.com) — Codex
