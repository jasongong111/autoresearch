# Autonomous Loop Protocol

Detailed protocol for the autoresearch iteration loop. SKILL.md has the summary; this file has the full rules.

## Loop Modes

Autoresearch supports two loop modes:

- **Unbounded (default):** Loop forever until manually interrupted (`Ctrl+C`)
- **Bounded:** Loop exactly N times when `Iterations: N` is set in the inline config (or `--iterations N` flag for CLI/CI)

When bounded, track `current_iteration` against `max_iterations`. After the final iteration, print a summary and stop.

## Phase 0: Precondition Checks (before loop starts)

**MUST complete ALL checks before entering the loop. Fail fast if any check fails.**

```bash
# 1. Run setup.sh if present in task folder
if [ -f "setup.sh" ]; then
    bash setup.sh
    # → If fails: warn user, fix or abort before entering loop
fi

# 2. Verify git repo exists
git rev-parse --git-dir 2>/dev/null || echo "FAIL: not a git repo"
# → If not a git repo: ask user to run `git init` or abort

# 3. Check for dirty working tree
git status --porcelain
# → If dirty: warn user and ask to stash or commit first
#   NEVER proceed with uncommitted user changes — explicit git add will stage them

# 4. Check for stale lock files
ls .git/index.lock 2>/dev/null && echo "WARN: stale lock"
# → If lock exists: remove it (rm .git/index.lock) or warn user

# 5. Check for detached HEAD
git symbolic-ref HEAD 2>/dev/null || echo "WARN: detached HEAD"
# → If detached: warn user, suggest `git checkout <branch>`

# 6. Check for git hooks that might interfere
ls .git/hooks/pre-commit .git/hooks/commit-msg 2>/dev/null && echo "INFO: git hook detected"
ls .husky/pre-commit .husky/commit-msg 2>/dev/null && echo "INFO: husky hook detected"
ls .pre-commit-config.yaml 2>/dev/null && echo "INFO: pre-commit framework detected"
# → If hooks exist: note in setup log. If hook blocks commits during loop,
#   treat as crash and log "hook blocked commit" — do NOT use --no-verify

# 7. Scaffold verify harness if missing (agent_core tasks)
test -f ./verify.sh || python "$REPO_ROOT/.claude/skills/autoresearch/scripts/scaffold_task_harness.py" --task-name "<task-folder-name>"

# 8. Baseline commit MUST include skills/** (critical for safe_revert)
test -f skills/*/SKILL.md || echo "FAIL: commit skills/ before first experiment"
# → If the first experiment only adds SKILL.md, git revert on discard deletes it entirely.

# 9. Confirm agent_core task binding (harness must pass task= matching folder name)
grep -q 'task=' tests/run_agent_eval.py || echo "WARN: run_agent_eval.py missing task= for agent_core"
```

**If metric-valued guard is configured** (has `Guard-Direction` and `Guard-Threshold`):

```bash
# 6. Extract guard-metric baseline
GUARD_BASELINE=$(<guard command>)
# Validate it's a valid number (same rules as verify metric)
# Record alongside the primary metric baseline in iteration 0
```

**If any FAIL:** Stop and inform user. Do not enter the loop with broken preconditions.
**If any WARN:** Log the warning, proceed with caution, inform user.

## Phase 1: Review (30 seconds)

Before each iteration, build situational awareness. **You MUST complete ALL 7 steps — git history and your own logs from the last round are critical for learning from past iterations.**

```
1. Read current state of in-scope files (full context)
2. Read last 10-20 entries from autoresearch-results.tsv (the results log you wrote in prior rounds)
3. Read the most recent record from `logs/experiment.jsonl` (the action log you wrote last round)
   — review hypothesis, filesModified, verifyOutput/guardOutput, status, and description
4. MUST run: git log --oneline -20 to see recent changes
5. MUST run: git diff HEAD~1 (if last iteration was "keep") to review what worked
6. Identify: what worked, what failed, what's untried — based on results log, experiment.jsonl, AND git history
7. If bounded: check current_iteration vs max_iterations
```

**Why read your logs every time?** The TSV results log records outcomes (metric, delta, keep/discard). The experiment action log records *what you actually did* — hypothesis, files touched, and truncated verify/guard output. Read both before ideating so you do not repeat a failed hypothesis or miss a clue in last round's verify output.

```bash
# Results log — recent outcomes
tail -20 autoresearch-results.tsv

# Last round's full action record (required every iteration after baseline)
tail -1 logs/experiment.jsonl

# Optional: scan last few rounds for repeating discard/crash patterns
tail -5 logs/experiment.jsonl
```

**Why read git history every time?** Git IS the memory. After rollbacks, state may differ from what you expect. The git log shows which experiments were kept vs reverted. The git diff of kept changes reveals WHAT specifically improved the metric — use this to inform the next iteration. Never assume — always verify.

**Git history usage pattern:**
- `git log --oneline -20` → see the sequence of experiments (kept commits remain, discarded ones are reverted)
- `git diff HEAD~1` → inspect the last kept change to understand WHY it worked
- `git log --all --oneline` → if working on a branch, see full experiment history
- Use commit messages (e.g., "experiment: increase batch size") to avoid repeating failed approaches

## Git as Memory — Configuration

Git as Memory is **always enabled** — it's a core behavior, not optional. The agent reads its own git history every iteration to learn from past experiments.

| Parameter | Default | Description |
|-----------|---------|-------------|
| Memory depth | 20 commits | How far back to read history |
| Diff review | HEAD~1 | How far back to diff kept changes |
| Full history | disabled | Read all branches |

At the start of every iteration (Phase 1), the agent runs:

```bash
tail -20 autoresearch-results.tsv        # recent outcomes
tail -1 logs/experiment.jsonl            # last round's action log
git log --oneline -20                    # what was tried (kept vs reverted)
git diff HEAD~1                          # exact diff that worked
git log --oneline -20 | grep "experiment" # all experiment descriptions
git show <hash> --stat                  # deep-dive a specific success
```

**Example:** Agent reads git log and sees:
- `a1b2c3d experiment(api): add response caching` — KEPT
- `Revert "experiment(api): increase cache TTL to 60s"` — REVERTED
- `c3d4e5f experiment(api): add cache invalidation on write` — KEPT

Agent learns: caching works, longer TTL doesn't. Next: try a different cache strategy, NOT longer TTL.

## Phase 2: Ideate (Strategic)

Pick the NEXT change. **MUST consult git history, results log, and the last `logs/experiment.jsonl` record before deciding.**

**How to use git as memory:**
- Run `git log --oneline -10` — read commit messages to see what was tried
- For each "keep" in results log, run `git show <commit-hash> --stat` to see what files/patterns worked
- For discarded approaches, read the commit message to understand what was attempted and avoid repeating it
- Read the last experiment.jsonl record — use `verifyOutput`, `hypothesis`, and `filesModified` to explain why the last round failed or succeeded
- Look for patterns: if 3 commits improved metric by touching file X, focus on file X

**Priority order:**

1. **Fix crashes/failures** from previous iteration first
2. **Exploit successes** — run `git diff` on last kept commit, try variants in same direction
3. **Explore new approaches** — cross-reference results log, experiment.jsonl, AND git history to find untried approaches
4. **Combine near-misses** — two changes that individually didn't help might work together
5. **Simplify** — remove code while maintaining metric. Simpler = better
6. **Radical experiments** — when incremental changes stall, try something dramatically different

**Anti-patterns:**
- Don't repeat exact same change that was already discarded — CHECK git log first
- Don't make multiple unrelated changes at once (can't attribute improvement)
- Don't chase marginal gains with ugly complexity
- Don't ignore git history — it's the primary learning mechanism between iterations

**Bounded mode consideration:** If remaining iterations are limited (<3 left), prioritize exploiting successes over exploration.

## Phase 3: Modify (One Atomic Change)

- Make ONE focused change to in-scope files
- The change should be explainable in one sentence
- Write the description BEFORE making the change (forces clarity)

### Three-Level Skill Optimization Policy

When optimizing an agent skill package, progress through these levels gradually. Start at the lowest level that directly addresses the failure evidence from Phase 1-2. Do not skip to a higher level just because it is more interesting, but also do not park on the same level indefinitely.

**No level parking:** Do not spend more than 3 consecutive iterations at the same level without either a kept improvement or an explicit escalation. If two attempts at the same level crash, produce no diff, or are discarded for the same reason, escalate on the next iteration. Record the level in the experiment description, for example: `level 1: add answer-normalizer script`.

#### Level 1: Outsource Procedural Tasks to Deterministic Code (`skills/<name>/scripts/`)

Use Level 1 when the skill relies on prose to perform strict algorithmic work, such as parsing files, validating JSON, normalizing answers, checking directory layouts, or running sequential calculations. Text instructions for these tasks eventually hallucinate, skip steps, or apply rules inconsistently.

**Action:** Identify the deterministic part of the workflow. Write a Python, Node, or Bash script under `skills/<name>/scripts/`, then replace the long prose procedure in `SKILL.md` with a short command contract.

**Before (text-based):**
```markdown
Look at the directory structure. Check if every folder has an index file. If a folder is missing one, list it out...
```

**After (script-based):**
```markdown
Run `python3 skills/<name>/scripts/audit_layout.py`. If the exit code is non-zero, parse the printed JSON error array and present it to the user.
```

Level 1 changes are preferred before adding more prompt text whenever the failure is procedural and mechanically checkable.

#### Level 2: Implement Progressive Disclosure (`skills/<name>/references/`)

Use Level 2 when `SKILL.md` is getting bloated with edge cases, lookup tables, formatting rules, domain FAQs, or long background explanations. The main skill should route behavior; heavy details should load only when needed.

**Action:** Move non-essential documentation into `skills/<name>/references/`, then add conditional gates in `SKILL.md` that say exactly when to read each reference and when not to.

```markdown
## Error Handling
If the linting script fails with a formatting error, read `references/STYLE_GUIDE.md`
to understand whitespace policies before suggesting a fix. Otherwise, do not read it.
```

Level 2 changes should reduce core prompt load while preserving retrieval precision.

#### Level 3: Bind Explicit Tooling and Define a Strict Exit Protocol

Use Level 3 when the agent is guessing which tool or command to use, looping over command variants, or failing to know when the skill is complete.

**Action:** Bind each step to the environment's concrete capabilities (shell commands, scripts, native tools, or MCP endpoints when available), and end the workflow with an unambiguous Definition of Done.

**Tool binding example:**
```markdown
Use the filesystem tool to write the output to `build.log`. Do not stream the full log back into chat.
```

**Exit protocol example:**
```markdown
The skill is complete only when `python3 scripts/verify.py` returns `status: 0`.
If you hit three consecutive non-zero returns, halt immediately, print the exact logs,
and yield control back to the user.
```

Level 3 changes should eliminate tool ambiguity and define hard stop conditions. Use this level after Level 1-2 have not stabilized execution, or when Phase 1 logs show repeated loops caused by unclear tooling or unclear completion criteria.

### Multi-File Atomic Changes

One logical change may span multiple files. This is still ONE change if it serves a single purpose.

**The one-sentence test:** If you need "and" to describe it, it's two changes. Split them.

| One Change (OK) | Two Changes (Split) |
|-----------------|---------------------|
| Change port 3000→8080 in Dockerfile + compose + nginx | Change port AND add new service |
| Update Node 18→20 in Dockerfile + CI + package.json | Update Node AND switch to pnpm |
| Add Redis in compose + app config + env vars | Add Redis AND refactor auth module |

#### DevOps Example

```bash
# Iteration 1: Enable Docker layer caching (2 files, one intent)
git add Dockerfile .github/workflows/ci.yml
git commit -m "experiment(ci): enable Docker layer caching"
# ✓ One change: "enable caching" — same intent across files

# Iteration 2: Parallelize test jobs (1 file)
git add .github/workflows/ci.yml
git commit -m "experiment(ci): parallelize tests with matrix strategy"
# ✓ One change: "parallelize tests"
```

### Enforcing Atomicity — Self-Check

```bash
# After modifying but before committing, validate atomicity:
FILES_CHANGED=$(git diff --name-only | wc -l)

# Heuristic: >5 files likely means multiple changes — review
if [ "$FILES_CHANGED" -gt 5 ]; then
  echo "WARN: ${FILES_CHANGED} files changed — verify single intent"
fi

# The one-sentence test: describe the change in ONE sentence
# If you need "and", split into separate iterations
```

### Atomicity

One logical change per iteration. Multi-file is fine if it serves a single purpose.

**The one-sentence test:** If you need "and" to describe it, it's two changes.

| Atomicity | Behavior | When to Use |
|-----------|----------|-------------|
| `strict` (default) | One logical change. Self-check before commit. Warn if >5 files. | Most optimization tasks |
| `relaxed` | Coordinated multi-file changes OK. Still requires one-sentence description. | Infrastructure/config spanning many files |

**Self-check before committing:**
```bash
FILES_CHANGED=$(git diff --name-only | wc -l)
# >5 files → re-evaluate: is this truly ONE change?
# Description contains "and" + action verb → SPLIT
```

## Phase 4: Commit (Before Verification)

**You MUST commit before running verification.** This enables clean rollback if the experiment fails.

```bash
# Stage ONLY in-scope files (safer than git add -A)
# List the specific files you modified and add them individually:
git add <file1> <file2> ...
# AVOID git add -A — it stages ALL files including .env, node_modules, and user's unrelated work

# Check if there's actually something to commit
git diff --cached --quiet
# → If exit code 0 (no staged changes): skip commit, log as "no-op", go to next iteration
# → If exit code 1 (changes exist): proceed with commit

# Commit with descriptive experiment message
git commit -m "experiment(<scope>): <one-sentence description of what you changed and why>"
```

**"Nothing to commit" handling:** If `git add <files>` followed by `git diff --cached --quiet` shows no changes, the modification phase produced no actual diff. This is NOT a crash — log as `status=no-op` with description of what was attempted, skip verification, and proceed to next iteration. Do NOT create an empty commit.

**WARNING:** NEVER use `git add -A` — it stages ALL files including .env, credentials, and user's unrelated work. Always use `git add <file1> <file2> ...` with explicit file paths. After staging, verify with `git diff --cached --name-only` that only in-scope files are staged.

**Commit message format:** Use conventional commit format with `experiment` type: `experiment(<scope>): <description>`. This keeps compatibility with commit-lint while clearly marking autoresearch iterations. Example: `experiment(auth): increase timeout from 5s to 30s — hypothesis: reduces flaky test failures`.

**Hook failure handling:** If a pre-commit hook blocks the commit:
1. Read the hook's error output to understand WHY it blocked
2. If fixable (lint error, formatting): fix the issue, re-stage, and retry the commit — do NOT use `--no-verify`
3. If not fixable within 2 attempts: log as `status=hook-blocked`, revert the in-scope file changes (`git checkout -- <files>`), and move to next iteration
4. NEVER bypass hooks with `--no-verify` — hooks exist to protect code quality

**Rollback strategy (if experiment fails):**
```bash
# Preferred: git revert (safe, preserves history)
git revert HEAD --no-edit

# Alternative: git reset (if revert conflicts)
git revert --abort && git reset --hard HEAD~1
```

**IMPORTANT:** Prefer `git revert` over `git reset --hard` — revert preserves the experiment in history (so you can learn from it), while reset destroys it. Use `git reset --hard` only if revert produces merge conflicts.

**Phase 4 safety:** If `git commit` itself fails for any reason (disk full, hook timeout, permissions), clean up staged changes before moving on:

```bash
git reset HEAD -- .   # unstage everything
git checkout -- <in-scope files>   # restore files to last committed state
# Log as status=crash, continue to next iteration
```

## Phase 5: Verify (Mechanical Only)

Run the agreed-upon verification command. In this repository, the Verify command loads `expected/eval.json`, runs each test case through `agent_core` with the skill under test on the gemma-4-e2b model, rates gemma4's output against the expectations, and prints a single metric number. Capture output.

**How eval.json verification works:**

1. The verify script (e.g., `./verify.sh`) reads `expected/eval.json` — an array of test cases, each with `id`, `name`, `prompt`, and `expectations`.
2. For each test case, it calls `python -m agent_core chat --task <task-name> <prompt>` or uses the programmatic `SkillAgentRunner` API.
3. `agent_core` discovers the skill from `tasks/<task-name>/skills/` and runs the prompt through the gemma-4-e2b model.
4. The scorer rates gemma4's output against each item in the `expectations` array (e.g., did it use the right API? did it include the required fields?).
5. The script aggregates the scores and prints exactly one number — the metric — to stdout.
6. The agent run trace is written to `logs/agent-core/agent_core_trace.jsonl` for inspection.

**Timeout rule:** If verification exceeds 2x normal time, kill and treat as crash.

**Extract metric:** Parse the verification output for the specific metric number.

**Metric validation (MANDATORY after extraction):**

The extracted value MUST be a valid number before ANY decision logic runs. A non-numeric value means the verify pipeline is broken — the agent must not guess, interpolate, or treat it as zero.

```
extracted_value = <result of verify pipeline>

# Strip leading/trailing whitespace and newlines before validation
extracted_value = strip(extracted_value)

# Validate: must match a number (integer or float, optional leading minus)
IF extracted_value does NOT match pattern: ^-?[0-9]+\.?[0-9]*$
    STATUS = "metric-error"
    LOG iteration as:
      status=metric-error
      description="Metric extraction returned non-numeric value: '{extracted_value}'"
    .claude/skills/autoresearch/scripts/safe_revert.sh

    # Diagnose: show the raw verify output so the problem is visible
    PRINT "⚠ Metric extraction failed — got '{extracted_value}' instead of a number"
    PRINT "Raw verify output (last 5 lines):"
    PRINT <tail -5 of verify command output>
    PRINT "Check your Verify command pipeline — the final output must be a single number"

    # If this is the 2nd consecutive metric-error, the verify command is broken.
    # Do NOT keep iterating with a broken pipeline.
    IF previous_iteration.status == "metric-error":
        PRINT "✗ Two consecutive metric extraction failures — verify command is broken. Stopping."
        STOP (even in unbounded mode)

    # Otherwise, proceed to next iteration (a transient failure is possible
    # if the codebase is in a state where the verify command can't run cleanly)
    CONTINUE to next iteration
```

**Valid statuses** now include `metric-error` alongside `keep`, `discard`, `crash`, `no-op`, `hook-blocked`.

### Verification Command Templates for agent_core + eval.json

These templates show common patterns for verifying a skill against an `eval.json` file. The actual Verify command is a script that wraps one of these patterns and extracts a single number.

| Pattern | Verify Command | Metric | Direction |
|---------|---------------|--------|-----------|
| **Pass rate** | `python run_eval.py --eval expected/eval.json --task <task>` | Fraction of cases passing all expectations | higher |
| **Expectation accuracy** | `python run_eval.py --eval expected/eval.json --task <task>` | Fraction of individual expectations met | higher |
| **Tool-use accuracy** | `python run_eval.py --eval expected/eval.json --task <task> --metric tools` | Tool calls correct | higher |
| **Latency** | `python run_eval.py --eval expected/eval.json --task <task> --metric latency` | Avg ms per case | lower |
| **Token efficiency** | `python run_eval.py --eval expected/eval.json --task <task> --metric tokens` | Avg tokens per case | lower |

**eval.json format:**

```json
[
  {
    "id": 1,
    "name": "test-case-name",
    "prompt": "The user prompt sent to agent_core",
    "expectations": [
      "The agent does not use SQL",
      "The agent queries the HTTP API",
      "The output includes the required fields"
    ]
  }
]
```

**Important:** The verify script must set `GEMMA4_API_KEY` (and optionally `GEMMA4_MODEL_ID`, `GEMMA4_BASE_URL`) before calling `agent_core`. The agent_core runner automatically discovers skills from `tasks/<task>/skills/` when `--task` is provided.

## Phase 5.1: Noise Handling (for Volatile Metrics)

Agent runs can be noisy — model temperature, non-deterministic tool ordering, or random seeds can produce slightly different outputs across runs. Use these strategies to prevent false keep/discard decisions.

| Strategy | When to use | Config |
|----------|-------------|--------|
| **Multi-run median** | High variance in pass rate across runs | `Noise: high` (3 runs) or `Noise-Runs: 5` |
| **Min-delta threshold** | Marginal improvements that could be noise | `Min-Delta: 0.05` — only keep if delta > threshold |
| **Confirmation run** | Unsure if improvement is real | Re-run verify; keep only if both agree |
| **Model pinning** | Non-deterministic outputs | Set `temperature=0`, fixed seeds, deterministic ordering |

**Preventing premature rollbacks:**
```
IF metric_worse AND abs(delta) < noise_floor:
    second_result = run_verify()
    IF second_result also worse: STATUS = "discard"
    ELSE: STATUS = "keep" ; LOG "NOISE: regression not confirmed"
```

## Phase 5.2: Selection Split Validation (Anti-Overfitting Gate)

A candidate skill that improves on the training split is **not** automatically accepted. It must also pass the selection validation before it can replace the previous best skill. The selection split runs `holdout/eval.json` through `agent_core` on the gemma-4-e2b model and scores gemma4's output against the expectations. This acts as a held-out generalization checkpoint.

**Configuration:**
```
/autoresearch
Goal: Maximize benchmark score
Verify: ./verify.sh                              # runs against expected/eval.json (training / dev split)
Selection-Verify: python run_eval.py --eval holdout/eval.json --task <task-name>
Direction: higher
```

**Why this matters:** Optimizing solely against a dev split invites overfitting — the skill memorizes training-case quirks rather than learning the underlying task. The selection split acts as a generalization checkpoint. The optimizer does not see holdout data during the training rollout, so performance there measures true skill improvement.

**When to run:** Phase 5.2 executes whenever the training-split metric from Phase 5 strictly improved relative to the best training metric. If training split did not improve, the candidate is already headed for discard — skip Phase 5.2 to save time.

**Protocol:**

```
IF training_metric did NOT improve:
    # Skip selection check — candidate will be discarded
    CONTINUE to Phase 6

IF Selection-Verify is configured:
    selection_command = Selection-Verify
ELSE:
    # Default: run holdout/eval.json through agent_core using the same runner as Verify
    selection_command = <same runner but pointed at holdout/eval.json>

selection_metric = run(selection_command)

# Validate selection metric is numeric (same rules as primary metric)
IF selection_metric does NOT match pattern: ^-?[0-9]+\.?[0-9]*$
    STATUS = "metric-error"
    DESCRIPTION = "Selection-Verify returned non-numeric value: '{selection_metric}'"
    .claude/skills/autoresearch/scripts/safe_revert.sh
    CONTINUE to Phase 7 (log)

# Strict improvement required on selection split
IF selection_metric is better than best_selection_metric (respecting Direction):
    STATUS = "keep"
    best_selection_metric = selection_metric
    best_training_metric = training_metric  # update training best too
    best_iteration = current_iteration
    iterations_since_best = 0
    # Commit stays. Proceed to Phase 7 (log).
ELSE:
    STATUS = "discard (selection)"
    REASON = "training split improved ({training_metric}) but selection split did not generalize ({selection_metric} vs best {best_selection_metric})"
    .claude/skills/autoresearch/scripts/safe_revert.sh
    # Proceed to Phase 7 (log)
```

**State tracking:**

Add these to the per-session state tracked across iterations:

| Variable | Initial Value | Updated When |
|----------|---------------|--------------|
| `best_training_metric` | Baseline from iteration 0 on Verify | Training split improves |
| `best_selection_metric` | Baseline from iteration 0 on Selection-Verify | Selection split improves |
| `best_iteration` | 0 | Either split sets a new best |

In the TSV log, `metric` records the **training** metric (the primary optimization signal). In the NDJSON experiment log, also record `selectionMetric` when available.

**Setup baseline for selection split:**

During Setup Step 8 (establish baseline):
1. Run the selection command against the current skill state
2. Validate the output is numeric
3. Record as `best_selection_metric` in iteration 0's log entry
4. If it fails or returns non-numeric, warn the user but do not block the loop

**Important rules:**
- Do NOT modify the skill between training verify and selection verify. Both commands evaluate the **same committed change**.
- The selection split command must be independent — it should not read or depend on results from the training verify.
- Selection split evaluation counts as part of the same iteration. It does not consume a separate iteration number.
- Never tune the skill directly against the selection split. Use it only as an acceptance gate, not as a gradient signal.

## Phase 5.5: Guard (Regression Check)

If a **guard** command was defined during setup, run it after verification.

The guard protects existing functionality while the main metric is being optimized. It operates in one of two modes:

**Pass/fail mode (default):** Guard is a command that must exit 0. Common examples: `npm test`, `npm run typecheck`, `pytest`, `cargo test`.

**Metric-valued mode:** Guard extracts a number (like the verify command) and checks it against a regression threshold. Use this when you need tolerance, not a binary tripwire. Example: "bundle size can grow up to 5% from baseline, but no more."

```
# Pass/fail guard (default):
Guard: npm test

# Metric-valued guard:
Guard: npx esbuild src/index.ts --bundle --minify | wc -c
Guard-Direction: lower is better
Guard-Threshold: 5%
```

**Key distinction:**
- **Verify** answers: "Did the metric improve?" (the goal)
- **Guard** answers: "Did anything else break?" (the safety net)

**Guard rules (both modes):**
- Only run if a guard was defined (it's optional)
- Run AFTER verify — no point checking guard if the metric didn't improve
- If guard fails, revert the optimization and try to rework it (max 2 attempts)
- NEVER modify guard/test files — always adapt the implementation instead
- Log guard failures distinctly so the agent can learn what kinds of changes cause regressions

**Pass/fail mode rules:**
- Exit code 0 = pass. Non-zero = fail.

**Metric-valued mode rules:**
- Extract the guard-metric using the same numeric validation as the primary metric (must match `^-?[0-9]+\.?[0-9]*$`)
- If guard-metric extraction fails, treat as guard failure (not metric-error)
- Compare against baseline using the threshold:
  ```
  IF Guard-Direction is "lower is better":
      guard_passed = (guard_metric <= guard_baseline * (1 + threshold/100))
      # Example: baseline 50000 bytes, threshold 5% → pass if <= 52500
  IF Guard-Direction is "higher is better":
      guard_passed = (guard_metric >= guard_baseline * (1 - threshold/100))
      # Example: baseline 95% coverage, threshold 5% → pass if >= 90.25%
  ```
- `Guard-Threshold: 0%` means strict no-regression: the guard-metric must not worsen at all from baseline.

**Guard failure recovery (max 2 rework attempts):**

When the guard fails but the metric improved, the optimization idea may still be viable — it just needs a different implementation that doesn't break behavior:

1. Revert the change (run `.claude/skills/autoresearch/scripts/safe_revert.sh`)
2. Read the guard output to understand WHAT broke (which tests, which assertions)
3. Rework the optimization to avoid the regression — e.g.:
   - If inlining a function broke callers → try a different optimization angle
   - If changing a data structure broke serialization → preserve the interface
   - If reordering logic broke edge cases → add the optimization more surgically
4. Commit the reworked version, re-run verify + guard
5. If both pass → keep. If guard fails again → one more attempt, then give up

**Critical:** Guard/test files are read-only. The optimization must adapt to the tests, never the other way around. If after 2 rework attempts the optimization can't pass the guard, discard it and move on to a different idea.

## Phase 6: Decide (No Ambiguity)

**Selection split short-circuit:** If Phase 5.2 ran and already set STATUS to `"keep"` or `"discard (selection)"`, skip directly to Phase 7 (Log Results). The selection split is the final arbiter — no further decision logic applies.

**Rollback:** Use the provided script for all discard/crash decisions:
```bash
.claude/skills/autoresearch/scripts/safe_revert.sh
```
This tries `git revert HEAD --no-edit` first (preserves history), and falls back to `git reset --hard HEAD~1` only if revert conflicts.

```
IF metric_improved AND (no guard OR guard_passed):
    STATUS = "keep"
    # Do nothing — commit stays. Git history preserves this success.
ELIF metric_improved AND guard_failed:
    .claude/skills/autoresearch/scripts/safe_revert.sh
    # Rework the optimization (max 2 attempts)
    FOR attempt IN 1..2:
        Analyze guard output → rework implementation (NOT tests)
        git add <modified-files> && git commit -m "experiment(<scope>): rework — <description>"
        Re-run verify
        IF metric_improved:
            Re-run guard
            IF guard_passed:
                STATUS = "keep (reworked)"
                BREAK
        .claude/skills/autoresearch/scripts/safe_revert.sh
    IF still failing after 2 attempts:
        STATUS = "discard"
        REASON = "guard failed, could not rework optimization"
ELIF metric_same_or_worse:
    STATUS = "discard"
    .claude/skills/autoresearch/scripts/safe_revert.sh
ELIF crashed:
    # Attempt fix (max 3 tries)
    IF fixable:
        Fix → re-commit → re-verify → re-guard
    ELSE:
        STATUS = "crash"
        .claude/skills/autoresearch/scripts/safe_revert.sh
```

**Why `git revert` instead of `git reset --hard`?**
- `git revert` preserves the failed experiment in history — this IS the "memory." Future iterations can read `git log` and see what was tried and failed.
- `git reset --hard` destroys the commit entirely — the agent loses memory of what was attempted.
- `git revert` is also safer in Claude Code — it's a non-destructive operation that doesn't trigger safety warnings.
- Fallback: if `git revert` produces merge conflicts, use `git revert --abort` then `git reset --hard HEAD~1`.

## Phase 7: Log Results

### 7a — Append to results log (TSV format)

```
iteration  commit   metric   status        description
42         a1b2c3d  0.9821   keep          increase attention heads from 8 to 12
43         -        0.9845   discard       switch optimizer to SGD
44         -        0.0000   crash         double batch size (OOM)
45         -        -        no-op         attempted to modify read-only config (no diff produced)
46         -        -        hook-blocked  pre-commit lint hook rejected formatting in model.py
```

**Valid statuses:** `keep`, `keep (reworked)`, `discard`, `discard (selection)`, `crash`, `no-op`, `hook-blocked`, `metric-error`

### 7b — Append to experiment action log (NDJSON format)

Use the provided script to write both TSV and NDJSON in one call:

```bash
python .claude/skills/autoresearch/scripts/log_iteration.py \
  --iteration 3 \
  --commit "b2c3d4e" \
  --metric 0.65 \
  --delta 0.05 \
  --guard pass \
  --status keep \
  --description "add API routing rules"
```

Optional fields to include when available:

| Field | When to include |
|-------|-----------------|
| `guardMetric` | When using a metric-valued guard |
| `selectionMetric` | When selection split validation was run |
| `hypothesis` | The agent's reasoning for why this change would work |
| `filesRead` | Array of files read during Phase 1–3 |
| `filesModified` | Array of files actually changed in Phase 3 |
| `toolsUsed` | Array of `{name, input}` objects for every tool call |
| `verifyOutput` | Last 500 chars of verify stdout/stderr (truncate if longer) |
| `guardOutput` | Last 500 chars of guard stdout/stderr (truncate if longer) |
| `durationMs` | Wall-clock time for the entire iteration |

Example full record:

```json
{
  "iteration": 3,
  "timestamp": "2026-05-24T12:10:00Z",
  "status": "discard",
  "commit": "-",
  "metric": 86.5,
  "delta": -0.6,
  "guard": "pass",
  "description": "refactor test helpers (broke 2 tests)",
  "hypothesis": "centralizing setup reduces duplication",
  "filesRead": ["src/auth.test.ts", "src/helpers.ts"],
  "filesModified": ["src/helpers.ts", "src/auth.test.ts"],
  "toolsUsed": [
    {"name": "Read", "input": {"file_path": "src/auth.test.ts"}},
    {"name": "Edit", "input": {"file_path": "src/helpers.ts"}}
  ],
  "verifyOutput": "Tests: 48 passed, 2 failed\n FAIL src/auth.test.ts",
  "durationMs": 42000
}
```

**Rules:**
- Write **both** the TSV row and the NDJSON record for every iteration (including baseline).
- Write them **immediately** after the keep/discard decision while context is fresh.
- Do NOT commit `logs/experiment.jsonl` to git (`logs/` should be gitignored).

## Phase 8: Repeat

### Unbounded Mode (default)

Go to Phase 1. **Do not ask "should I keep going?" — keep iterating unless a halt condition fires** (see Plateau Detection below).

### Bounded Mode (with Iterations: N)

```
IF current_iteration < max_iterations:
    Go to Phase 1
ELIF goal_achieved:
    Print: "Goal achieved at iteration {N}! Final metric: {value}"
    Print final summary
    STOP
ELSE:
    Print final summary
    STOP
```

**Final summary format:**
```
=== Autoresearch Complete (N/N iterations) ===
Baseline: {baseline} → Final: {current} ({delta})
Keeps: X | Discards: Y | Crashes: Z | Skipped: W (no-ops + hook-blocked)
Best iteration: #{n} — {description}
```

### When Stuck (>5 consecutive discards)

Applies to both modes:
1. Re-read ALL in-scope files from scratch
2. Re-read the original goal/direction
3. Review entire results log for patterns
4. Try combining 2-3 previously successful changes
5. Try the OPPOSITE of what hasn't been working
6. Try a radical architectural change

### Plateau Detection (unbounded mode)

"Stuck" catches consecutive discards, but a subtler failure mode exists: the agent keeps iterating, occasionally getting a `keep`, yet the *best* metric never actually improves. The loop burns tokens without making real progress.

Track two values across iterations:

```
best_metric       = baseline metric from iteration 0
best_iteration    = 0
iterations_since_best = 0
plateau_patience  = 15  (default, configurable via Plateau-Patience: N)
```

Update after every iteration where a valid metric was extracted:

```
IF new_metric is better than best_metric (respecting Direction):
    best_metric = new_metric
    best_iteration = current_iteration
    iterations_since_best = 0
ELSE:
    iterations_since_best += 1
```

Skip iterations with no valid metric (`no-op`, `metric-error`, `hook-blocked`, `crash`) — they don't count toward the patience window because the agent didn't get a real signal.

**When `iterations_since_best >= plateau_patience`:**

```
PRINT "⚠ Plateau detected — best metric has not improved in {plateau_patience} iterations"
PRINT "  Best: {best_metric} (iteration #{best_iteration})"
PRINT "  Current: {current_metric}"
PRINT "  Last {plateau_patience} iterations: {keeps} keeps, {discards} discards — no net gain"

AskUserQuestion:
  question: "The metric has plateaued. How do you want to proceed?"
  header: "Plateau Detected"
  options:
    - label: "Stop here"
      description: "End the loop. Best metric: {best_metric} at iteration #{best_iteration}"
    - label: "Continue with reset patience"
      description: "Keep going for another {plateau_patience} iterations before checking again"
    - label: "Change strategy"
      description: "I'll adjust the goal, scope, or verify command"
```

**Configuration:**

```
/autoresearch
Goal: Reduce bundle size below 200KB
Verify: npx esbuild src/index.ts --bundle --minify | wc -c
Plateau-Patience: 20    # check after 20 iterations without improvement (default: 15)
```

Set `Plateau-Patience: off` to disable plateau detection entirely and restore the original unbounded behavior. Use this for overnight runs where you accept the token cost.

**Bounded mode:** Plateau detection is disabled. The iteration limit already bounds the run, and the agent should use all N iterations to explore.

## Crash Recovery

### Within an iteration (verify command failures)

- Syntax error → fix immediately, don't count as separate iteration
- Runtime error → attempt fix (max 3 tries), then move on
- Resource exhaustion (OOM) → revert, try smaller variant
- Infinite loop/hang → kill after timeout, revert, avoid that approach
- External dependency failure → skip, log, try different approach

### Session crash (agent itself dies mid-iteration)

If the agent crashes (API timeout, context window exhaustion, user kills the process), the working tree may be in a partially modified state. On the next invocation, Phase 0 precondition checks will detect this. Here's how to recover depending on what state git is in:

**Detect state:**

```bash
# 1. Uncommitted changes in working tree?
DIRTY=$(git status --porcelain)

# 2. Last commit is an unverified experiment?
LAST_MSG=$(git log --oneline -1)
# If it starts with "experiment(" and there's no corresponding results log entry,
# the agent crashed after commit but before verify/decide.
```

**Recovery rules:**

```
IF working tree is dirty (changes not yet committed):
    # Agent crashed during Phase 3 (modify) — before commit
    # These changes were never verified. Discard them.
    git checkout -- <in-scope files>
    LOG "Recovered from session crash: discarded uncommitted modifications"
    Resume loop from Phase 1

IF last commit is "experiment(...)" with no matching results log entry:
    # Agent crashed after Phase 4 (commit) but before Phase 6 (decide)
    # The experiment was never verified. Revert it.
    .claude/skills/autoresearch/scripts/safe_revert.sh
    LOG "Recovered from session crash: reverted unverified experiment"
    Resume loop from Phase 1

IF working tree is clean AND last commit has a results log entry:
    # Agent crashed after Phase 7 (log) — clean state
    # Nothing to recover. Resume normally.
    Resume loop from Phase 1
```

## Communication

- **DO NOT** ask "should I keep going?" — in unbounded mode, keep iterating unless a halt condition fires (plateau detection, two consecutive metric-errors). In bounded mode, continue until N is reached.
- **DO NOT** summarize after each iteration — just log and continue
- **DO** print a brief one-line status every ~5 iterations (e.g., "Iteration 25: metric at 0.95, 8 keeps / 17 discards")
- **DO** alert if you discover something surprising or game-changing
- **DO** print a final summary when bounded loop completes
