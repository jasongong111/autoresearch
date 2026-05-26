"""Discover skill markdown files in the autoresearch repo."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class SkillDoc:
    id: str
    path: str
    name: str
    category: str
    source: str
    last_modified: float
    size: int

    def to_dict(self) -> Dict[str, str | float | int]:
        return {
            "id": self.id,
            "path": self.path,
            "name": self.name,
            "category": self.category,
            "source": self.source,
            "lastModified": self.last_modified,
            "size": self.size,
        }


SKILL_GLOBS = [
    ".claude/skills/**/*.md",
    ".claude/commands/**/*.md",
    ".agents/skills/**/*.md",
    "plugins/autoresearch/skills/**/*.md",
    "plugins/autoresearch/resources/**/*.md",
    "plugins/autoresearch/scripts/**/*.md",
]


def discover_skills(repo_root: Path) -> List[SkillDoc]:
    """Find all skill markdown files under the repo root."""
    repo_root = repo_root.resolve()
    docs: List[SkillDoc] = []
    seen: set[str] = set()

    for pattern in SKILL_GLOBS:
        for path in sorted(repo_root.glob(pattern)):
            if not path.is_file():
                continue
            key = str(path.resolve())
            if key in seen:
                continue
            seen.add(key)
            rel = path.relative_to(repo_root).as_posix()
            parts = rel.split("/")
            category = _infer_category(parts)
            source = parts[0] if parts else ""
            stat = path.stat()
            docs.append(
                SkillDoc(
                    id=rel,
                    path=str(path),
                    name=path.stem,
                    category=category,
                    source=source,
                    last_modified=stat.st_mtime,
                    size=stat.st_size,
                )
            )

    docs.sort(key=lambda d: (d.category, d.name))
    return docs


def _infer_category(parts: List[str]) -> str:
    if len(parts) >= 3 and parts[-2] == "references":
        return "reference"
    if len(parts) >= 3 and parts[-2] == "commands":
        return "command"
    if len(parts) >= 2 and parts[-1] == "SKILL.md":
        return "skill"
    if "scripts" in parts:
        return "script"
    if "resources" in parts:
        return "resource"
    return "other"


def read_skill_content(repo_root: Path, doc_id: str) -> Optional[str]:
    """Read the raw markdown content of a skill doc by its relative id."""
    repo_root = repo_root.resolve()
    path = repo_root / doc_id
    try:
        path = path.resolve()
        # security: ensure the resolved path is still under repo_root
        if not str(path).startswith(str(repo_root)):
            return None
        if not path.is_file():
            return None
        return path.read_text(encoding="utf-8")
    except (OSError, ValueError):
        return None
