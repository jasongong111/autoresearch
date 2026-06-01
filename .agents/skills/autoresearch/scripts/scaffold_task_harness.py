#!/usr/bin/env python3
"""Scaffold agent_core verify harness files in a task folder.

Usage (from repo root or task root):
    python .claude/skills/autoresearch/scripts/scaffold_task_harness.py --task-name simple-lookups

Creates verify.sh, selection-verify.sh, and tests/run_agent_eval.py.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent / "templates"


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold agent_core task harness files.")
    parser.add_argument(
        "--task-name",
        required=True,
        help="Task folder name (must match tasks/<name>/ and agent_core task=)",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    task_root = Path.cwd()
    if task_root.name != args.task_name:
        candidate = Path("tasks") / args.task_name
        if candidate.is_dir():
            task_root = candidate.resolve()
        else:
            print(
                f"Run from tasks/{args.task_name}/ or repo root with tasks/{args.task_name}/ present",
                file=sys.stderr,
            )
            return 1

    (task_root / "tests").mkdir(parents=True, exist_ok=True)

    copies = [
        (TEMPLATES / "verify.sh", task_root / "verify.sh"),
        (TEMPLATES / "selection-verify.sh", task_root / "selection-verify.sh"),
        (TEMPLATES / "run_agent_eval.py", task_root / "tests" / "run_agent_eval.py"),
    ]

    eval_template = (TEMPLATES / "run_agent_eval.py").read_text(encoding="utf-8")
    eval_content = eval_template.replace("__TASK_NAME__", args.task_name)

    for src, dest in copies:
        if dest.exists() and not args.force:
            print(f"skip (exists): {dest}")
            continue
        if src.name == "run_agent_eval.py":
            dest.write_text(eval_content, encoding="utf-8")
        else:
            shutil.copy2(src, dest)
        dest.chmod(0o755)
        print(f"wrote: {dest}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
