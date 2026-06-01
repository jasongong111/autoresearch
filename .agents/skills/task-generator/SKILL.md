---
name: task-generator
description: >-
  ALWAYS activate when the user wants to convert an existing skill into an
  autoresearch task for optimization. Triggers: "transfer to task",
  "make this a task", "convert to autoresearch task", "optimize this skill",
  "set up for autoresearch", "taskify", or any request to prepare a skill for
  the autoresearch loop.
version: 1.0.0
---

# Task Generator — Convert a Skill for Autoresearch Optimization

**Core idea:** Take an existing skill and restructure it into a self-contained task folder that the autoresearch loop can optimize against a measurable metric.

## When to Activate

- User says "transfer this to a task", "make this optimizable", "set up for autoresearch"
- User wants to run `/autoresearch` on an existing skill that isn't yet a task
- User asks to "taskify" a skill
- User wants to optimize a skill but there's no `tasks/<name>/` folder or `README.md`

## Prerequisites

- An existing skill package (`SKILL.md` + `references/` + optional `scripts/` and `assets/`)
- A way to evaluate the skill (benchmark prompts + scoring logic)

## The Conversion Process

### 1. Choose a Task Name

Pick a short, descriptive, kebab-case name:

```
gemma4-math-skill-optimization
api-error-formatter
docs-consistency-checker
```

Create the task folder:

```bash
mkdir -p tasks/<task-name>
cd tasks/<task-name>
```

### 2. Copy the Skill Package

Copy the skill into the task folder. This is the only editable target during optimization.

```
tasks/<task-name>/
└── skills/<name>/       # EDITABLE — optimizer target
    ├── SKILL.md         # Core routing and behavior
    ├── references/      # Optional: deep docs, FAQs, examples
    ├── scripts/         # Optional: deterministic CLIs
    └── assets/          # Optional: templates, configs, boilerplate
```

### 3. Create Eval Data

Create benchmark prompts and expectations in `eval.json` format.

```
tasks/<task-name>/
├── skills/<name>/
├── expected/            # READ-ONLY — dev eval set
│   └── eval.json        # Prompts + expectations (scored against agent output)
└── holdout/             # READ-ONLY — hidden eval set
    └── eval.json        # Final validation — never tune against
```

**`eval.json` format:**

```json
[
  {
    "prompt": "Realistic user task...",
    "expectations": [
      "The output contains a table with at least 5 rows",
      "The generated code uses pandas.read_csv"
    ]
  }
]
```

Split prompts at an **80:20 ratio**:
- **~80%** into `expected/eval.json` (dev set, visible during optimization)
- **~20%** into `holdout/eval.json` (hidden set, final validation only)

#### Writing good eval prompts

Prompts should be realistic tasks that a real user would give. Include file paths, personal context, specific values, and casual phrasing.

**Bad:** "Format this data"

**Good:** "ok so my boss just sent me this xlsx file (its in my downloads, called something like 'Q4 sales final FINAL v2.xlsx') and she wants me to add a column that shows the profit margin as a percentage"

Write 3–5 prompts to start. Expand later.

#### Writing good expectations

Expectations are verifiable statements about the output.

Good expectations are:
- **Objectively verifiable** — a script or grader can check them unambiguously
- **Descriptive** — they read clearly in the benchmark viewer
- **Skill-discriminating** — they should tend to pass with the skill and fail without it

**Good examples:**
- "The output file `report.pdf` contains a table with at least 5 rows"
- "The generated code uses the `pandas.read_csv` function"
- "The response includes a `timing.json` file with `duration_ms` field"

**Bad examples:**
- "The output is good" (subjective)
- "The skill was used" (not verifiable from output)
- "The result is correct" (vague)

Do not write assertions for subjective skills — rely on human review instead.

#### Validate the eval suite

Before finishing, sanity-check:
1. **Coverage** — Do prompts exercise the main paths? If the skill has branches, at least one eval should hit each.
2. **Verifiability** — Can every expectation be checked by a script without human judgment?
3. **Discrimination** — Would a naive solution likely fail at least one expectation per eval?

### 4. Write `input.md` (Optional)

If every eval prompt shares common context (e.g., "You are working in a React project"), put it in `input.md` at the task root. The evaluation harness merges this prefix with each prompt before sending to the agent.

### 5. Create `setup.sh` (Optional but Recommended)

If the skill or evaluation harness needs dependencies, create `setup.sh`:

```bash
#!/bin/bash
set -e
cd "$(dirname "$0")"

# Initialize git if missing
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  git init
  git add .
  git commit -m "baseline: initial task state"
fi

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

echo "Task setup complete."
```

### 6. Write the Task README

Create `README.md` with these sections. The autoresearch loop reads this file for configuration.

```markdown
# <Task Name>

## Goal
One sentence: what are we optimizing?

## Metric
What number does the Verify command produce?

## Direction
Higher is better or lower is better?

## Scope
What files may the optimizer edit?
What files must stay read-only?

## Verify
The command that runs the dev eval set and prints a single metric number.
Example: `./verify.sh`

## Baseline
Current metric: X.XX (run before first optimization)

## Target
Desired metric: Y.YY (optional aspiration)

## Instructions
Any task-specific rules, formatting requirements, or constraints.
```

### 7. Initialize Git

Each task folder must be an independent git repo:

```bash
cd tasks/<task-name>
git init
git add .
git commit -m "baseline: initial task state"
```

**Do not** nest this inside the parent autoresearch repo's git history. The task folder must be its own repo so the loop can `git revert` experiments freely.

Add to the parent repo's `.gitignore`:

```
tasks/*/
!tasks/*/README.md
tasks/*/.autoresearch/
tasks/*/autoresearch-results.tsv
tasks/*/__pycache__/
tasks/*/logs/
```

### 8. Run Setup

If you created `setup.sh`, run it now:

```bash
cd tasks/<task-name>
./setup.sh
```

Otherwise, initialize git manually and create a virtual environment:

```bash
cd tasks/<task-name>
git init && git add . && git commit -m "baseline: initial task state"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 9. Launch the Loop

Now the task is ready. From the autoresearch repo root:

```bash
./bin/autoresearch-cursor \
  --project tasks/<task-name> \
  --goal "Improve <metric> on <task>" \
  --scope "skills/**" \
  --metric "<metric> (<direction>)" \
  --verify "./verify.sh" \
  --iterations 20
```

Or invoke the autoresearch skill directly:

```text
/autoresearch
Goal: <goal>
Scope: skills/**
Metric: <metric>
Direction: <higher|lower> is better
Verify: ./verify.sh
Iterations: 20
```

## Task Folder Reference

### Full structure

```
tasks/<task-name>/
├── README.md                 # Task goal, verify command, editable scope
├── input.md                  # Optional: instructions merged with each prompt
├── skills/                   # EDITABLE — optimizer target
│   └── <skill-name>/
│       ├── SKILL.md
│       ├── references/
│       ├── scripts/
│       └── assets/
├── expected/                 # READ-ONLY — dev eval set
│   └── eval.json
├── holdout/                  # READ-ONLY — hidden eval set
│   └── eval.json
├── requirements.txt          # Optional: Python deps
├── setup.sh                  # Optional: one-time environment setup
├── autoresearch-results.tsv  # Generated — iteration log (gitignored)
└── logs/                     # Generated — runtime traces (gitignored)
    ├── agent-core/
    │   └── agent_core_trace.jsonl
    ├── session.json
    ├── trace.jsonl
    └── experiment.jsonl
```

### Roles and edit boundaries

| Area | Role | Optimizer may edit? |
|------|------|---------------------|
| `skills/**` | Skill package under test | **Yes** |
| `expected/**` | Dev eval set | **No** |
| `holdout/**` | Hidden final eval | **No** — do not read during the loop |
| `input.md` | Shared prompt prefix | **No** |
| `logs/**` | Runtime traces | **No** — write-only metadata |
| `autoresearch-results.tsv` | Iteration history | Append only |

### Autoresearch helper scripts

The autoresearch skill provides scripts in `.claude/skills/autoresearch/scripts/`:

| Script | Purpose |
|--------|---------|
| `init_task.py` | Initialize logs, TSV, and run baseline verify |
| `log_iteration.py` | Append a result to TSV and NDJSON logs |
| `safe_revert.sh` | Safe `git revert` with fallback |
| `run_eval.py` | Generic eval.json runner via agent_core |

## Safety Posture

- Never copy secrets (`.env`, API keys) into a task folder
- Keep `holdout/` truly hidden — do not reference it in `README.md` instructions
- Verify that `git rev-parse --git-dir` succeeds inside the task folder before launching the loop
- Scope the editable target narrowly; huge scopes confuse the optimizer

## Checklist

Before declaring a task ready:

- [ ] Task folder exists at `tasks/<task-name>/`
- [ ] `README.md` has Goal, Metric, Direction, Scope, Verify sections
- [ ] `skills/<name>/SKILL.md` is the editable target
- [ ] `expected/eval.json` has enough prompts to show signal
- [ ] `holdout/eval.json` exists and is never read during optimization
- [ ] `setup.sh` installs deps and initializes git (or done manually)
- [ ] `git rev-parse --git-dir` succeeds and has a baseline commit
- [ ] Baseline metric is recorded in `README.md`
- [ ] Parent repo `.gitignore` excludes generated task artifacts
