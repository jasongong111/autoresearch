"""Discover and invoke agent skills from the filesystem."""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


@dataclass
class SkillInfo:
    name: str
    description: str
    path: Path
    scripts: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)


def _unfold_block(lines: list[str], start_idx: int) -> tuple[str, int]:
    """Collect indented lines after a block scalar indicator (>-, >, |-)."""
    i = start_idx + 1
    min_indent: int | None = None
    raw_lines: list[str] = []
    while i < len(lines):
        line = lines[i]
        if line.strip() == "":
            raw_lines.append("")
            i += 1
            continue
        stripped = line.lstrip(" ")
        indent = len(line) - len(stripped)
        if min_indent is None:
            min_indent = indent
        if indent < min_indent and stripped:
            break
        raw_lines.append(stripped)
        i += 1
    # Folded scalar: join lines with spaces, preserve blank lines as paragraph breaks
    result_parts: list[str] = []
    for idx, rl in enumerate(raw_lines):
        if rl == "":
            result_parts.append("\n")
        else:
            result_parts.append(rl)
            # Append a space if the next line is also non-blank (folded behavior)
            if idx + 1 < len(raw_lines) and raw_lines[idx + 1] != "":
                result_parts.append(" ")
    return "".join(result_parts).strip(), i - 1


def parse_frontmatter(text: str) -> dict[str, str]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}

    meta: dict[str, str] = {}
    lines = match.group(1).splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if ":" not in line:
            i += 1
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value in (">-", ">", "|-", "|"):
            folded, i = _unfold_block(lines, i)
            meta[key] = folded
        else:
            meta[key] = value.strip('"').strip("'")
        i += 1
    return meta


def discover_skills(*roots: Path) -> List[SkillInfo]:
    """Scan skill roots and return unique skills by frontmatter name.

    Supports two layouts:
      - Standard: <root>/<skill-name>/SKILL.md
      - Flat:     <root>/<skill-name>.md
    """
    found: dict[str, SkillInfo] = {}

    for root in roots:
        if not root.is_dir():
            continue
        for entry in sorted(root.iterdir()):
            if entry.is_dir():
                skill_md = entry / "SKILL.md"
                if not skill_md.is_file():
                    continue
                meta = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
                name = meta.get("name") or entry.name
                scripts_dir = entry / "scripts"
                scripts = (
                    sorted(path.name for path in scripts_dir.iterdir() if path.is_file())
                    if scripts_dir.is_dir()
                    else []
                )
                references_dir = entry / "references"
                references = (
                    sorted(path.name for path in references_dir.iterdir() if path.is_file() and path.suffix.lower() == ".md")
                    if references_dir.is_dir()
                    else []
                )
                found[name] = SkillInfo(
                    name=name,
                    description=meta.get("description", ""),
                    path=entry.resolve(),
                    scripts=scripts,
                    references=references,
                )
            elif entry.is_file() and entry.suffix.lower() == ".md":
                name = entry.stem
                meta = parse_frontmatter(entry.read_text(encoding="utf-8"))
                found[name] = SkillInfo(
                    name=meta.get("name") or name,
                    description=meta.get("description", ""),
                    path=entry.resolve(),
                    scripts=[],
                    references=[],
                )

    return list(found.values())


def format_skill_catalog(skills: List[SkillInfo]) -> str:
    if not skills:
        return "No skills discovered."

    lines = ["Available skills (these are NOT tools — use read_skill to learn about them):"]
    for skill in skills:
        hints: List[str] = []
        if skill.scripts:
            hints.append(f"scripts={', '.join(skill.scripts)}")
        if skill.references:
            hints.append(f"references={', '.join(skill.references)}")
        hint = " " + " ".join(hints) if hints else ""
        lines.append(f"- {skill.name}: {skill.description}{hint}")
    return "\n".join(lines)


class SkillRegistry:
    """Runtime registry for skill discovery and invocation."""

    def __init__(self, *roots: Path) -> None:
        self.roots = roots
        self.skills = discover_skills(*roots)
        self._by_name = {skill.name: skill for skill in self.skills}

    def refresh(self) -> None:
        self.skills = discover_skills(*self.roots)
        self._by_name = {skill.name: skill for skill in self.skills}

    def catalog(self) -> str:
        return format_skill_catalog(self.skills)

    def list_skills(self) -> str:
        return self.catalog()

    def read_skill(self, skill_name: str) -> str:
        skill = self._by_name.get(skill_name)
        if skill is None:
            known = ", ".join(sorted(self._by_name)) or "(none)"
            return f"Error: unknown skill '{skill_name}'. Known skills: {known}"

        if skill.path.is_file() and skill.path.suffix.lower() == ".md":
            return skill.path.read_text(encoding="utf-8")
        skill_md = skill.path / "SKILL.md"
        return skill_md.read_text(encoding="utf-8")

    def read_skill_reference(self, skill_name: str, ref_name: str) -> str:
        skill = self._by_name.get(skill_name)
        if skill is None:
            known = ", ".join(sorted(self._by_name)) or "(none)"
            return f"Error: unknown skill '{skill_name}'. Known skills: {known}"

        references_root = (skill.path / "references").resolve()
        ref_path = (references_root / ref_name).resolve()
        if references_root not in ref_path.parents and ref_path != references_root:
            return "Error: invalid reference path"
        if not ref_path.is_file():
            available = ", ".join(skill.references) or "(none)"
            return f"Error: reference '{ref_name}' not found. Available: {available}"
        return ref_path.read_text(encoding="utf-8")

    def run_skill_script(
        self,
        skill_name: str,
        script_name: str,
        args: Optional[List[str]] = None,
    ) -> str:
        skill = self._by_name.get(skill_name)
        if skill is None:
            return f"Error: unknown skill '{skill_name}'"

        scripts_root = (skill.path / "scripts").resolve()
        script_path = (scripts_root / script_name).resolve()
        if scripts_root not in script_path.parents and script_path != scripts_root:
            return "Error: invalid script path"
        if not script_path.is_file():
            available = ", ".join(skill.scripts) or "(none)"
            return f"Error: script '{script_name}' not found. Available: {available}"

        command = [sys.executable, str(script_path), *(args or [])]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            cwd=str(skill.path),
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
            return f"Error: script exited {result.returncode}: {detail}"
        return result.stdout.strip() or "(script produced no output)"
