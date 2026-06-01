#!/usr/bin/env python3
"""Run expected or holdout evals through agent_core; print accuracy to stdout."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[1]
TASK_NAME = "__TASK_NAME__"

load_dotenv(TASK_ROOT / ".env")
load_dotenv(REPO_ROOT / ".env")
sys.path.insert(0, str(REPO_ROOT))

from agent_core.runner import SkillAgentRunner  # noqa: E402


def load_cases(eval_path: Path) -> list[dict]:
    data = json.loads(eval_path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "evals" in data:
        return data["evals"]
    if isinstance(data, list):
        return data
    raise ValueError(f"Unsupported eval format: {eval_path}")


def _numbers(text: str) -> list[str]:
    return [re.sub(r"[, $]", "", m) for m in re.findall(r"\$?[\d,]+(?:\.\d+)?", text)]


def _quoted_strings(text: str) -> list[str]:
    return [m.group(1) or m.group(2) for m in re.finditer(r"'([^']+)'|\"([^\"]+)\"", text)]


def check_expectation(answer: str, expectation: str) -> bool:
    answer_l = answer.lower()
    for num in _numbers(expectation):
        if num and num in re.sub(r"[, $]", "", answer):
            return True
    for phrase in _quoted_strings(expectation):
        if phrase.lower() in answer_l:
            return True
    tokens = [w.lower() for w in re.findall(r"[a-zA-Z]{4,}", expectation)]
    if tokens and sum(1 for t in tokens if t in answer_l) >= max(1, len(tokens) // 2):
        return True
    return False


def score_case(answer: str, case: dict) -> bool:
    expectations = case.get("expectations") or []
    if not expectations:
        expected = (case.get("expected_output") or "").strip()
        if not expected:
            return bool(answer.strip())
        return expected.lower() in answer.lower()
    return all(check_expectation(answer, exp) for exp in expectations)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["expected", "holdout"], default="expected")
    parser.add_argument("--output", default=None, help="Write per-case JSON results")
    args = parser.parse_args()

    eval_path = TASK_ROOT / args.split / "evals.json"
    cases = load_cases(eval_path)
    trace_dir = TASK_ROOT / "logs" / "agent-core"
    trace_dir.mkdir(parents=True, exist_ok=True)

    runner = SkillAgentRunner(
        trace_path=trace_dir / "agent_core_trace.jsonl",
        verbose=False,
    )

    correct = 0
    results: list[dict] = []
    started = time.perf_counter()

    for case in cases:
        prompt = case["prompt"]
        session_id = f"eval-{args.split}-{case.get('id', len(results) + 1)}"
        result = runner.run(prompt, task=TASK_NAME, session_id=session_id)
        answer = result.answer or ""
        ok = score_case(answer, case)
        correct += int(ok)
        results.append(
            {
                "id": case.get("id"),
                "prompt": prompt,
                "answer": answer,
                "correct": ok,
                "expectations": case.get("expectations", []),
            }
        )

    runner.close()
    accuracy = correct / len(cases) if cases else 0.0

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(
                {
                    "split": args.split,
                    "accuracy": accuracy,
                    "elapsed_seconds": time.perf_counter() - started,
                    "results": results,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    print(f"{accuracy:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
