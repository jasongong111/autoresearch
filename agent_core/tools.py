"""Function tools for skill discovery and invocation."""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path
from typing import Annotated, Dict, List, Optional

from agents import function_tool

from .registry import SkillRegistry


def _resolve_path(base_path: Path, relative_path: str) -> Path:
    """Resolve a user-provided relative path, blocking directory traversal."""
    target = (base_path / relative_path).resolve()
    base = base_path.resolve()
    if not str(target).startswith(str(base)):
        raise ValueError(f"Path escapes base directory: {relative_path}")
    return target


def build_tools(registry: SkillRegistry, base_path: str = ".") -> list:
    """Create OpenAI Agents SDK function tools bound to a registry."""
    _base = Path(base_path)

    @function_tool
    def list_skills() -> str:
        """List available agent skills with names, descriptions, and script filenames."""
        return registry.list_skills()

    @function_tool
    def read_skill(
        skill_name: Annotated[str, "Skill name from list_skills, e.g. gemma3-delegate"],
    ) -> str:
        """Read the SKILL.md instructions for a skill by name."""
        return registry.read_skill(skill_name)

    @function_tool
    def read_skill_reference(
        skill_name: Annotated[str, "Skill name from list_skills"],
        ref_name: Annotated[str, "Reference filename from the skill's references/ directory"],
    ) -> str:
        """Read a markdown reference file from a skill's references/ directory."""
        return registry.read_skill_reference(skill_name, ref_name)

    @function_tool(strict_mode=False)
    def run_skill_script(
        skill_name: Annotated[str, "Skill name from list_skills"],
        script_name: Annotated[str, "Script filename from the skill's scripts/ directory"],
        args: Annotated[
            Optional[List[str]],
            "Optional CLI arguments passed to the script as a JSON array of strings. Omit this key if there are no arguments.",
        ] = None,
    ) -> str:
        """Run an executable script from a skill's scripts/ directory."""
        # Defensive: coerce a single string into a list
        if isinstance(args, str):
            args = [args]
        return registry.run_skill_script(skill_name, script_name, args)

    @function_tool
    def exec_command(
        command: Annotated[str, "Command to execute. Dangerous commands will be rejected."],
        timeout: Annotated[Optional[int], "Maximum seconds to wait for the command."] = 60,
    ) -> str:
        """Execute a command and return its stdout, stderr, and exit code."""
        try:
            cmd_parts = shlex.split(command)
        except ValueError as e:
            return f"Error: invalid command syntax: {e}"

        if not cmd_parts:
            return "Error: empty command."

        dangerous = {"rm", "curl", "wget", "sudo", "chmod", "chown", "mv", "dd", "mkfs"}
        executable = os.path.basename(cmd_parts[0])
        if executable in dangerous:
            return f"Blocked: '{executable}' is not allowed."

        try:
            result = subprocess.run(
                cmd_parts, shell=False, capture_output=True, text=True, timeout=timeout
            )
            output = result.stdout.strip()
            error = result.stderr.strip()
            parts = [f"exit_code: {result.returncode}"]
            if output:
                parts.append(f"stdout:\n{output}")
            if error:
                parts.append(f"stderr:\n{error}")
            return "\n\n".join(parts)
        except subprocess.TimeoutExpired:
            return f"Timed out after {timeout}s."
        except Exception as e:
            return f"Error: {e}"

    @function_tool
    def read_file(
        file_path: Annotated[str, "Relative file path from the project root."],
        offset: Annotated[Optional[int], "1-based line number to start reading from."] = None,
        limit: Annotated[Optional[int], "Maximum number of lines to read."] = None,
    ) -> str:
        """Read the contents of a file, optionally from a specific line offset."""
        try:
            target = _resolve_path(_base, file_path)
            if not target.is_file():
                return f"Error: {file_path} is not a file."
            text = target.read_text(encoding="utf-8")
            lines = text.splitlines()
            start = (offset - 1) if offset else 0
            end = start + limit if limit else len(lines)
            selected = lines[start:end]
            prefix = f"Lines {start + 1}-{start + len(selected)} of {len(lines)}\n"
            return prefix + "\n".join(selected)
        except Exception as e:
            return f"Error reading {file_path}: {e}"

    @function_tool
    def write_file(
        file_path: Annotated[str, "Relative file path from the project root."],
        content: Annotated[str, "Full content to write to the file."],
    ) -> str:
        """Write content to a file, creating parent directories if needed."""
        try:
            target = _resolve_path(_base, file_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return f"Wrote {len(content)} characters to {file_path}."
        except Exception as e:
            return f"Error writing {file_path}: {e}"

    @function_tool
    def edit_file(
        file_path: Annotated[str, "Relative file path from the project root."],
        old_string: Annotated[str, "Exact existing string to replace. Must be unique in the file."],
        new_string: Annotated[str, "New string to insert in its place."],
    ) -> str:
        """Apply a targeted string replacement to a file (safe multi-line edit)."""
        try:
            target = _resolve_path(_base, file_path)
            if not target.is_file():
                return f"Error: {file_path} is not a file."
            text = target.read_text(encoding="utf-8")
            if text.count(old_string) != 1:
                return f"Error: old_string appears {text.count(old_string)} times (expected exactly 1)."
            text = text.replace(old_string, new_string, 1)
            target.write_text(text, encoding="utf-8")
            return f"Patched {file_path}."
        except Exception as e:
            return f"Error patching {file_path}: {e}"

    @function_tool
    def list_directory(
        dir_path: Annotated[str, "Relative directory path from the project root. Use '.' for root."],
    ) -> str:
        """List files and directories inside the given path."""
        try:
            target = _resolve_path(_base, dir_path)
            if not target.is_dir():
                return f"Error: {dir_path} is not a directory."
            entries = sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name))
            lines = [f"{'[DIR] ' if e.is_dir() else '      '}{e.name}" for e in entries]
            return "\n".join(lines) if lines else "(empty directory)"
        except Exception as e:
            return f"Error listing {dir_path}: {e}"

    @function_tool(strict_mode=False)
    def fetch_url(
        url: Annotated[str, "URL to fetch. Only http and https are allowed."],
        method: Annotated[str, "HTTP method (GET, POST, PUT, DELETE, HEAD, OPTIONS, PATCH). Default: GET."] = "GET",
        headers: Annotated[Optional[Dict[str, str]], "Optional HTTP headers as a JSON object."] = None,
        body: Annotated[Optional[str], "Optional request body for POST, PUT, or PATCH."] = None,
        timeout: Annotated[int, "Maximum seconds to wait for the response."] = 30,
    ) -> str:
        """Fetch a URL over HTTP(S) and return the response body."""
        import json
        from urllib.error import HTTPError, URLError
        from urllib.parse import urlparse
        from urllib.request import Request, urlopen

        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return "Blocked: only http and https URLs are allowed."
        if not parsed.netloc:
            return "Error: invalid URL."

        method = method.upper()
        safe_methods = {"GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"}
        if method not in safe_methods:
            return f"Blocked: unsupported HTTP method '{method}'."

        req_headers = {}
        if headers is not None:
            if isinstance(headers, str):
                try:
                    req_headers = json.loads(headers)
                except json.JSONDecodeError:
                    return "Error: headers must be a valid JSON object."
            elif isinstance(headers, dict):
                req_headers = headers
            else:
                return "Error: headers must be a valid JSON object."

        req = Request(url, method=method, headers=req_headers)
        if body is not None and method in ("POST", "PUT", "PATCH"):
            req.data = body.encode("utf-8")

        try:
            with urlopen(req, timeout=timeout) as resp:
                content = resp.read()
                content_type = resp.headers.get("Content-Type", "").lower()
                if "application/json" in content_type:
                    try:
                        return json.dumps(json.loads(content), indent=2)
                    except (json.JSONDecodeError, ValueError):
                        pass
                try:
                    return content.decode("utf-8")
                except UnicodeDecodeError:
                    return content.decode("utf-8", errors="replace")
        except HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:2000]
            return f"HTTP {e.code} {e.reason}\n{body}"
        except URLError as e:
            return f"URL error: {e.reason}"
        except Exception as e:
            return f"Error: {e}"

    @function_tool
    def apply_patch(
        patch: Annotated[str, "Unified diff string to apply."],
        strip: Annotated[int, "Number of leading path components to strip (default 1)."] = 1,
    ) -> str:
        """Apply a unified diff patch across the repository using the `patch` command."""
        import re

        # Validate that all patched files stay within the base directory.
        target_lines = [ln for ln in patch.splitlines() if ln.startswith("+++") or ln.startswith("---")]
        path_re = re.compile(r"^\+\+\+\s+(\S+)")
        for line in target_lines:
            m = path_re.match(line)
            if not m:
                continue
            raw_path = m.group(1)
            # Strip leading prefix components (e.g., a/, b/)
            parts = raw_path.split("/")
            relative = "/".join(parts[strip:]) if strip < len(parts) else raw_path
            if not relative or relative.startswith("..") or relative.startswith("/"):
                return f"Blocked: invalid patch target path: {raw_path}"
            try:
                target = _resolve_path(_base, relative)
            except ValueError as exc:
                return f"Blocked: path escapes base directory: {raw_path} ({exc})"
            if not str(target).startswith(str(_base.resolve())):
                return f"Blocked: path escapes base directory: {raw_path}"

        try:
            result = subprocess.run(
                ["patch", f"-p{strip}", "--no-backup-if-mismatch"],
                cwd=_base,
                input=patch,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                return f"patch failed (exit {result.returncode}):\n{result.stderr.strip()}"
            return f"Patch applied.\n{result.stdout.strip()}"
        except FileNotFoundError:
            return "Error: `patch` command not found."
        except Exception as e:
            return f"Error applying patch: {e}"

    return [list_skills, read_skill, read_skill_reference, run_skill_script, exec_command, read_file, write_file, edit_file, list_directory, fetch_url, apply_patch]
