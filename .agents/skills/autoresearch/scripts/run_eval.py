#!/usr/bin/env python3
"""Run an eval.json through agent_core and print a metric.

Usage:
    python run_eval.py --eval expected/evals.json --task simple-lookups

Metric is printed to stdout only (safe for init_task.py). Logs go to stderr when --verbose.
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path


def load_cases(eval_path: Path) -> list[dict]:
    data = json.loads(eval_path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "evals" in data:
        return data["evals"]
    if isinstance(data, list):
        return data
    raise ValueError(f"Unsupported eval format: {eval_path}")


def score_output(answer: str, expectations: list[str]) -> tuple[int, int]:
    """Default expectation scorer. Returns (passed, total)."""
    passed = 0
    for expectation in expectations:
        nums = [re.sub(r"[, $]", "", m) for m in re.findall(r"\$?[\d,]+(?:\.\d+)?", expectation)]
        if nums and any(n in re.sub(r"[, $]", "", answer) for n in nums if n):
            passed += 1
            continue
        quoted = re.findall(r"'([^']+)'|\"([^\"]+)\"", expectation)
        if quoted and any((a or b).lower() in answer.lower() for a, b in quoted):
            passed += 1
            continue
        keywords = [w.lower() for w in expectation.split() if len(w) > 3]
        if keywords and any(k in answer.lower() for k in keywords):
            passed += 1
        elif not keywords:
            passed += 1
    return passed, len(expectations)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run eval.json through agent_core.")
    parser.add_argument("--eval", required=True, help="Path to eval.json")
    parser.add_argument("--task", required=True, help="Task name (tasks/<task>/skills/)")
    parser.add_argument("--metric", default="pass-rate", choices=["pass-rate", "expectation-accuracy"])
    parser.add_argument("--output", default=None, help="Write per-case results to this JSON file")
    parser.add_argument("--trace-dir", default="logs/agent-core", help="Directory for agent_core traces")
    parser.add_argument("--verbose", action="store_true", help="Print agent traces to stderr")
    args = parser.parse_args()

    eval_path = Path(args.eval)
    if not eval_path.is_file():
        print(f"Eval file not found: {eval_path}", file=sys.stderr)
        return 1

    cases = load_cases(eval_path)

    try:
        repo_root = Path(__file__).resolve().parents[4]
        sys.path.insert(0, str(repo_root))
        from agent_core.runner import SkillAgentRunner
    except Exception as exc:
        print(f"Failed to import agent_core: {exc}", file=sys.stderr)
        return 1

    os.makedirs(args.trace_dir, exist_ok=True)
    runner = SkillAgentRunner(
        trace_path=Path(args.trace_dir) / "agent_core_trace.jsonl",
        verbose=args.verbose,
    )

    total_passed = 0
    total_expectations = 0
    total_cases = len(cases)
    cases_passed = 0
    results = []

    start = time.perf_counter()
    for case in cases:
        prompt = case["prompt"]
        expectations = case.get("expectations", [])
        session_id = f"eval-{eval_path.stem}-{case.get('id', len(results) + 1)}"

        result = runner.run(prompt, task=args.task, session_id=session_id)
        answer = result.answer or ""

        passed, total = score_output(answer, expectations)
        total_passed += passed
        total_expectations += total
        if passed == total and total > 0:
            cases_passed += 1

        results.append(
            {
                "id": case.get("id"),
                "name": case.get("name"),
                "prompt": prompt,
                "answer": answer,
                "passed": passed,
                "total": total,
                "status": "pass" if passed == total and total > 0 else "fail",
            }
        )

    runner.close()
    elapsed = time.perf_counter() - start

    if args.output:
        with open(args.output, "w") as f:
            json.dump(
                {
                    "task": args.task,
                    "metric": args.metric,
                    "elapsed_seconds": elapsed,
                    "cases": results,
                },
                f,
                indent=2,
            )

    if args.metric == "pass-rate":
        metric = cases_passed / total_cases if total_cases else 0.0
    else:
        metric = total_passed / total_expectations if total_expectations else 0.0

    print(f"{metric:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
