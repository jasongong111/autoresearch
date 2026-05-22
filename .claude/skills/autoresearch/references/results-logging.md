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
BASELINE=$(npx jest --coverage 2>&1 | grep 'All files' | awk '{print $4}')

# 4. Record baseline as iteration 0
COMMIT=$(git rev-parse --short HEAD)
echo -e "0\t${COMMIT}\t${BASELINE}\t0.0\tpass\tbaseline\tinitial state — coverage ${BASELINE}%" >> autoresearch-results.tsv
```

### Optional: session metadata for the dashboard

At loop start (Phase 0), you may write `.autoresearch/session.json` so the [monitoring dashboard](../../../dashboard/README.md) can show run configuration without parsing chat:

```bash
mkdir -p .autoresearch
cat > .autoresearch/session.json <<'EOF'
{
  "goal": "Increase test coverage from 72% to 90%",
  "scope": "src/**/*.ts",
  "metric": "coverage %",
  "verify": "npx jest --coverage 2>&1 | grep 'All files' | awk '{print $4}'",
  "command": "autoresearch",
  "startedAt": "2026-05-21T14:00:00Z"
}
EOF
```

This file is local metadata (add `.autoresearch/` to `.gitignore` if desired). The dashboard reads it read-only.

### Optional: agent trace for the dashboard

Append structured events to `.autoresearch/trace.jsonl` (NDJSON, one object per line) so the dashboard can show a live agent trace alongside iteration metrics:

```bash
mkdir -p .autoresearch

# At loop start
echo '{"ts":"2026-05-21T14:00:00Z","iteration":0,"phase":"setup","message":"Baseline recorded","level":"info"}' >> .autoresearch/trace.jsonl

# During each phase (review, modify, verify, decide, log, etc.)
log_trace() {
  local iteration=$1 phase=$2 message=$3 level=${4:-info} detail=${5:-}
  local ts
  ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  if [ -n "$detail" ]; then
    printf '{"ts":"%s","iteration":%s,"phase":"%s","message":"%s","detail":"%s","level":"%s"}\n' \
      "$ts" "$iteration" "$phase" "$message" "$detail" "$level" >> .autoresearch/trace.jsonl
  else
    printf '{"ts":"%s","iteration":%s,"phase":"%s","message":"%s","level":"%s"}\n' \
      "$ts" "$iteration" "$phase" "$message" "$level" >> .autoresearch/trace.jsonl
  fi
}

log_trace 1 review "Read last 5 log entries — auth tests improved metric twice"
log_trace 1 modify "Added boundary tests for auth token expiry" info "src/auth.test.ts"
log_trace 1 verify "Verify returned 87.1 (+1.9)"
log_trace 1 decide "keep — metric improved, guard passed" success
```

| Field | Required | Description |
|-------|----------|-------------|
| `ts` | Yes | ISO 8601 timestamp |
| `phase` | Yes | Loop phase: `setup`, `review`, `ideate`, `modify`, `commit`, `verify`, `guard`, `decide`, `log`, or `info` |
| `message` | Yes | One-line summary of what the agent did or observed |
| `iteration` | No | Iteration number (use `round` for predict/reason) |
| `round` | No | Round number for swarm commands |
| `detail` | No | File path, command output snippet, or extra context |
| `level` | No | `info` (default), `success`, `failure`, or `warning` |

Subcommands that write markdown trace files (`persona-debates.md`, `judge-transcripts.md`, `lineage.md`, etc.) are also surfaced automatically in the dashboard when their TSV log is selected.

### Optional: trace analytics events

The dashboard also accepts richer Langfuse-like events in the same `.autoresearch/trace.jsonl` file. These events are optional and can be mixed with the simple loop events above. Use `type` (or `eventType`) to identify the record:

```json
{"ts":"2026-05-21T14:00:00Z","type":"trace","id":"t1","name":"research-loop","userId":"alice","latencyMs":1200}
{"ts":"2026-05-21T14:01:00Z","type":"observation","id":"o1","traceId":"t1","name":"plan","observationType":"generation","level":"DEFAULT","model":"gpt-5.5","userId":"alice","usage":{"input":1000,"output":500,"total":1500},"cost":{"input":0.01,"output":0.02,"total":0.03},"latencyMs":800}
{"ts":"2026-05-21T14:02:00Z","type":"score","traceId":"t1","name":"quality","source":"API","dataType":"NUMERIC","value":1}
```

| Event type | Key fields | Enables |
|------------|------------|---------|
| `trace` | `id`, `name`, `userId`, `latencyMs` or `startTime`/`endTime` | Trace count, trace count by name/user, trace latency percentiles |
| `observation` | `id`, `traceId`, `name`, `observationType`, `level`, `latencyMs` | Observation count by level, observation latency percentiles |
| `observation` with `observationType: "generation"` | `model`, `usage`, `cost`, `userId`, `latencyMs` | Model costs, model usage, user token cost, generation latency, model latency time series |
| `score` | `name`, `source`, `dataType`, `value` | Score summary, moving averages, histograms, categorical breakdowns |

Supported aliases: `eventType` for `type`, `modelName` for `model`, `latency_ms`/`durationMs`/`duration_ms` for `latencyMs`. Timestamps are bucketed hourly for time-series charts. `usage` and `cost` should be objects with optional `input`, `output`, and `total` values; if `total` is missing, the dashboard sums the provided detail fields.

### Agent conversations in the dashboard

The dashboard reads full agent conversations (user messages, assistant text, thinking, tool calls, MCP calls, tool results) from:

1. **Cursor auto-detect** — `~/.cursor/projects/{project-slug}/agent-transcripts/` (including subagent sessions)
2. **Explicit path** — `./bin/autoresearch-dashboard --transcripts-dir /path/to/agent-transcripts`
3. **Project mirror** — `.autoresearch/conversation.jsonl` (NDJSON, same format as Cursor exports)

Cursor may redact extended thinking as `[REDACTED]` in exported JSONL; explicit `thinking` blocks are shown when present.

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
Phase 1 (Review):   → READ last 10-20 log entries for pattern recognition
Phase 3-6 (Loop):   → Modify, Commit, Verify, Decide
Phase 7 (Log):      → APPEND new row after keep/discard/crash decision
Phase 8 (Repeat):   → Back to Phase 1 (reads updated log)
```

Complete end-to-end example:

```
/autoresearch
Goal: Increase test coverage from 72% to 90%
Scope: src/**/*.ts
Verify: npx jest --coverage 2>&1 | grep 'All files' | awk '{print $4}'
Guard: npm run typecheck

# Internal lifecycle:
# 1. Agent creates autoresearch-results.tsv with baseline 72.0
# 2. Agent reads log (empty except baseline) → decides first experiment
# 3. Agent modifies code, commits, runs verify → gets 74.5
# 4. Agent appends: "1  b2c3d4e  74.5  +2.5  pass  keep  add auth middleware tests"
# 5. Next iteration: agent reads log, sees auth tests worked → tries similar pattern
# 6. Continues until coverage reaches 90% or iterations exhausted
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

## Log Management

- Create at setup (iteration 0 = baseline)
- Append after EVERY iteration (including crashes)
- Do NOT commit this file to git (add to .gitignore)
- Read last 10-20 entries at start of each iteration for context
- Use to detect patterns: what kind of changes tend to succeed?

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
