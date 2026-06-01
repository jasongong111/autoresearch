#!/usr/bin/env bash
# Safe revert for autoresearch experiments.
# Preferred: git revert (preserves history).
# Fallback: git reset --hard HEAD~1 (if revert conflicts).
#
# After revert, restores skills/ from the pre-experiment parent commit so
# discard does not leave an empty skills/ tree when the first experiment
# only added files that were not in the baseline commit.
set -euo pipefail

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "ERROR: not a git repository" >&2
  exit 1
fi

PARENT=$(git rev-parse HEAD^)
LAST_MSG=$(git log --oneline -1)
echo "Reverting: $LAST_MSG"

revert_ok=false
if git revert HEAD --no-edit 2>/dev/null; then
  echo "Reverted via git revert (experiment preserved in history)"
  revert_ok=true
else
  echo "Revert conflicted — falling back to git reset --hard HEAD~1"
  git revert --abort 2>/dev/null || true
  git reset --hard HEAD~1
  PARENT=$(git rev-parse HEAD)
  echo "Reverted via reset (experiment removed from history)"
  revert_ok=true
fi

if [[ "$revert_ok" == true ]] && git cat-file -e "${PARENT}^{tree}" 2>/dev/null; then
  if git ls-tree -r --name-only "$PARENT" -- skills 2>/dev/null | grep -q .; then
    git checkout "$PARENT" -- skills/
    echo "Restored skills/ from pre-experiment commit $(git rev-parse --short "$PARENT")"
  fi
fi

if ! find skills -name 'SKILL.md' 2>/dev/null | grep -q .; then
  echo "WARN: no skills/**/SKILL.md after revert." >&2
  echo "  Commit the full skills/ package in your baseline before the first experiment." >&2
  echo "  Otherwise discard can delete skills that only existed in the reverted commit." >&2
fi
