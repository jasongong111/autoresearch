# Results Logging Protocol

Track every iteration in a structured log. Enables pattern recognition and prevents repeating failed experiments.

## Setup & Initialization

Autoresearch creates the log automatically at Phase 0 (baseline). The agent runs these commands during initialization:

```bash
# 1. Create log file with metric direction and header
echo "# metric_direction: higher_is_better" > autoresearch-results.tsv
echo -e "iteration\tcommit\tmetric\tdelta\tguard\tguard-metric\tstatus\tdescription" >> autoresearch-results.tsv

# 2. Add to .gitignore (log is local, not committed)
echo "autoresearch-results.tsv" >> .gitignore

# 3. Run verify command to establish baseline metric
BASELINE=$(./verify.sh)

# 4. Record baseline as iteration 0
COMMIT=$(git rev-parse --short HEAD)
echo -e "0\t${COMMIT}\t${BASELINE}\t0.0\tpass\t-\tbaseline\tinitial state — metric ${BASELINE}" >> autoresearch-results.tsv
```

## Logging Function

Called at Phase 7 of every iteration after the keep/discard/crash decision:

```bash
# Function: log_iteration
log_iteration() {
  local iteration=$1 commit=$2 metric=$3 delta=$4 guard=$5 guard_metric=$6 status=$7 description=$8
  echo -e "${iteration}\t${commit}\t${metric}\t${delta}\t${guard}\t${guard_metric}\t${status}\t${description}" \
    >> autoresearch-results.tsv
}

# Usage examples:
log_iteration 1 "b2c3d4e" "87.1" "+1.9" "pass" "-" "keep" "add tests for auth middleware"
log_iteration 2 "-" "86.5" "-0.6" "-" "-" "discard" "refactor test helpers (broke 2 tests)"
log_iteration 3 "-" "0.0" "0.0" "-" "-" "crash" "add integration tests (DB connection failed)"
log_iteration 4 "-" "-" "-" "-" "-" "no-op" "attempted to modify read-only config"
log_iteration 5 "-" "-" "-" "-" "-" "hook-blocked" "pre-commit lint rejected formatting"
log_iteration 6 "-" "-" "-" "-" "-" "metric-error" "verify output was 'PASS' — not a number"
```

## Reading & Using the Log

```bash
# Phase 1 (Review): Read recent entries for pattern recognition
tail -20 autoresearch-results.tsv
tail -1 logs/experiment.jsonl

# Count outcomes for progress tracking
KEEPS=$(grep -c 'keep' autoresearch-results.tsv || echo 0)
DISCARDS=$(grep -c 'discard' autoresearch-results.tsv || echo 0)
CRASHES=$(grep -c 'crash' autoresearch-results.tsv || echo 0)

# Detect stuck state: >5 consecutive discards triggers recovery
LAST_5=$(tail -5 autoresearch-results.tsv | awk -F'\t' '{print $6}')
# If all 5 are "discard" → trigger "When Stuck" protocol (re-read all files, try radical change)

# Pattern recognition: which file changes succeed?
# Cross-reference "keep" rows with git log to find winning patterns
grep 'keep' autoresearch-results.tsv | awk -F'\t' '{print $7}'
# → Shows descriptions of all successful changes
```

## Integration with the Autoresearch Loop

Where logging fits in the loop lifecycle:

```
Phase 0 (Setup):    → CREATE log file, record baseline (iteration 0)
Phase 1 (Review):   → READ last 10-20 TSV rows AND last experiment.jsonl record
Phase 3-6 (Loop):   → Modify, Commit, Verify, Decide
Phase 7 (Log):      → APPEND TSV row + experiment.jsonl record after keep/discard/crash decision
Phase 8 (Repeat):   → Back to Phase 1 (reads updated logs)
```

Complete end-to-end example:

```
/autoresearch
Goal: Maximize Gemma 4 E2B pass rate on the dev eval set
Scope: skills/**/*
Verify: ./verify.sh
Guard: ./scripts/check-evaluator-integrity.sh

# Internal lifecycle:
# 1. Agent creates autoresearch-results.tsv with baseline 0.60
# 2. Agent reads log (empty except baseline) → decides first experiment
# 3. Agent modifies skill, commits, runs verify → gets 0.65
# 4. Agent appends: "1  b2c3d4e  0.65  +0.05  pass  keep  add API routing rules"
# 5. Next iteration: agent reads log, sees routing rules worked → tries similar pattern
# 6. Continues until pass rate plateaus or iterations exhausted
```

## Log Format (TSV)

Create `autoresearch-results.tsv` in the working directory (gitignored):

```tsv
iteration	commit	metric	delta	guard	guard-metric	status	description
```

### Columns

| Column | Type | Description |
|--------|------|-------------|
| iteration | int | Sequential counter starting at 0 (baseline) |
| commit | string | Short git hash (7 chars), "-" if reverted |
| metric | float | Measured value from verification |
| delta | float | Change from previous best (negative = improved for "lower is better") |
| guard | enum | `pass`, `fail`, or `-` (no guard configured) |
| guard-metric | float or `-` | Measured guard-metric value (metric-valued guards only). `-` for pass/fail guards or no guard. |
| status | enum | `baseline`, `keep`, `keep (reworked)`, `discard`, `crash`, `no-op`, `hook-blocked`, `metric-error` |
| description | string | One-sentence description of what was tried |

### Example (pass/fail guard)

```tsv
iteration	commit	metric	delta	guard	guard-metric	status	description
0	a1b2c3d	85.2	0.0	pass	-	baseline	initial state — test coverage 85.2%
1	b2c3d4e	87.1	+1.9	pass	-	keep	add tests for auth middleware edge cases
2	-	86.5	-0.6	-	-	discard	refactor test helpers (broke 2 tests)
3	-	0.0	0.0	-	-	crash	add integration tests (DB connection failed)
4	-	88.9	+1.8	fail	-	discard	inline hot-path functions (guard: 3 tests broke)
5	c3d4e5f	88.3	+1.2	pass	-	keep	add tests for error handling in API routes
6	d4e5f6g	89.0	+0.7	pass	-	keep	add boundary value tests for validators
```

### Example (metric-valued guard — bundle size with 5% threshold)

```tsv
iteration	commit	metric	delta	guard	guard-metric	status	description
0	a1b2c3d	85.2	0.0	pass	48200	baseline	coverage 85.2%, bundle 48200 bytes
1	b2c3d4e	87.1	+1.9	pass	48500	keep	add auth tests (bundle +300 bytes, within 5%)
2	-	88.0	+0.9	fail	51500	discard	add integration tests (bundle +3300, exceeds 5% of 48200)
3	c3d4e5f	87.8	+0.7	pass	47900	keep	add unit tests (bundle decreased)
```

**Note:** When guard fails, the metric may have improved but the change is still discarded. The guard column makes this visible in the log. For metric-valued guards, the guard-metric column lets you track drift over time even when individual iterations stay within threshold.

## Experiment Action Log (`experiment.jsonl`)

Append a structured NDJSON record to `logs/experiment.jsonl` at the end of **every iteration** (including baseline). This file captures *what the agent did* — files read, tools used, hypothesis, and full result — so you can reconstruct the exact agent actions later.

### Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `iteration` | int | Yes | Iteration number (0 for baseline) |
| `timestamp` | string | Yes | ISO 8601 UTC timestamp |
| `status` | string | Yes | `baseline`, `keep`, `keep (reworked)`, `discard`, `crash`, `no-op`, `hook-blocked`, `metric-error` |
| `commit` | string | Yes | Short git hash, or `"-"` if reverted/no-op |
| `metric` | float \| null | Yes | Metric value, or `null` for no-op/crash/metric-error |
| `delta` | float \| null | Yes | Change from previous best, or `null` |
| `guard` | string | Yes | `pass`, `fail`, or `"-"` |
| `guardMetric` | float \| null | No | Guard-metric value if metric-valued guard is used |
| `description` | string | Yes | One-sentence description of the change |
| `hypothesis` | string | No | Why the agent thought this change would work |
| `filesRead` | string[] | No | Files the agent read during review/ideation |
| `filesModified` | string[] | No | Files actually modified in this iteration |
| `toolsUsed` | object[] | No | Tools invoked: `{name, input}` |
| `verifyOutput` | string | No | Last 500 chars of verify command stdout/stderr |
| `guardOutput` | string | No | Last 500 chars of guard command stdout/stderr |
| `durationMs` | int | No | Total iteration duration in milliseconds |

### Minimal record (keep)

```json
{"iteration":1,"timestamp":"2026-05-24T12:00:00Z","status":"keep","commit":"b2c3d4e","metric":87.1,"delta":1.9,"guard":"pass","description":"add tests for auth middleware edge cases"}
```

### Full record (discard with context)

```json
{
  "iteration": 2,
  "timestamp": "2026-05-24T12:05:00Z",
  "status": "discard",
  "commit": "-",
  "metric": 86.5,
  "delta": -0.6,
  "guard": "pass",
  "description": "refactor test helpers (broke 2 tests)",
  "hypothesis": "centralizing test setup will reduce duplication",
  "filesRead": ["src/auth.test.ts", "src/helpers.ts"],
  "filesModified": ["src/helpers.ts", "src/auth.test.ts"],
  "toolsUsed": [
    {"name": "Read", "input": {"file_path": "src/auth.test.ts"}},
    {"name": "Edit", "input": {"file_path": "src/helpers.ts"}}
  ],
  "verifyOutput": "Tests: 48 passed, 2 failed\n FAIL src/auth.test.ts\n  ● should reject expired token",
  "durationMs": 42000
}
```

### Shell helper

```bash
log_experiment() {
  local iteration=$1 status=$2 commit=$3 metric=$4 delta=$5 guard=$6 description=$7
  local ts
  ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  mkdir -p logs
  printf '{"iteration":%s,"timestamp":"%s","status":"%s","commit":"%s","metric":%s,"delta":%s,"guard":"%s","description":"%s"}\n' \
    "$iteration" "$ts" "$status" "$commit" "${metric:-null}" "${delta:-null}" "$guard" "$description" \
    >> logs/experiment.jsonl
}

# Usage:
log_experiment 1 "keep" "b2c3d4e" "87.1" "1.9" "pass" "add auth tests"
log_experiment 2 "discard" "-" "86.5" "-0.6" "pass" "refactor helpers (broke 2 tests)"
```

**Rules:**
- Write the record **immediately after** appending to `autoresearch-results.tsv` (Phase 7).
- Always write a record, even for `no-op`, `crash`, and `metric-error`.
- Do NOT commit this file to git (`logs/` should be gitignored).

## Log Management

- Create at setup (iteration 0 = baseline)
- Append after EVERY iteration (including crashes) — both TSV and `logs/experiment.jsonl`
- Do NOT commit these files to git (add to `.gitignore`)
- At Phase 1 (Review): read last 10-20 TSV rows **and** `tail -1 logs/experiment.jsonl`
- Use both logs to detect patterns: what kind of changes tend to succeed, and what verify output explained failures?

## Summary Reporting

Every 10 iterations (or at loop completion in bounded mode), print a brief summary:

```
=== Autoresearch Progress (iteration 20) ===
Baseline: 85.2% → Current best: 92.1% (+6.9%)
Keeps: 8 | Discards: 10 | Crashes: 2
Last 5: keep, discard, discard, keep, keep
```

## Metric Direction

Clarify at setup whether lower or higher is better:
- **Lower is better:** val_bpb, response time (ms), bundle size (KB), error count
- **Higher is better:** test coverage (%), lighthouse score, throughput (req/s)

Record direction in first line of results log as a comment:
```
# metric_direction: higher_is_better
```
