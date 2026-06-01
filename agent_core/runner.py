"""OpenAI Agents SDK runner with dynamic skill discovery via function tools."""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from agents import (
    Agent,
    AsyncOpenAI,
    ItemHelpers,
    ModelSettings,
    OpenAIChatCompletionsModel,
    RunConfig,
    Runner,
    SQLiteSession,
    set_tracing_disabled,
)
from agents.items import MessageOutputItem, ToolCallItem, ToolCallOutputItem
from agents.run_config import CallModelData, ModelInputData
from dotenv import load_dotenv
from openai.types.responses import ResponseTextDeltaEvent

from .logger import AgentLogger, LogCallback, serialize_model_input
from .paths import REPO_ROOT, SESSION_DB, TRACE_LOG, default_skill_roots
from .registry import SkillRegistry
from .metrics import RunMetricsTracker, extract_run_metrics
from .tools import build_tools

load_dotenv(REPO_ROOT / ".env")

DEFAULT_GEMMA4_MODEL = "google/gemma-4-E2B-it"
DEFAULT_GEMMA4_BASE_URL = "https://api-lm.tr-dev.work/v1"

GEMMA4_MODEL = os.environ.get("GEMMA4_MODEL_ID", DEFAULT_GEMMA4_MODEL)
GEMMA4_BASE_URL = os.environ.get("GEMMA4_BASE_URL", DEFAULT_GEMMA4_BASE_URL)
GEMMA4_API_KEY = os.environ.get("GEMMA4_API_KEY")
AGENT_MODEL = GEMMA4_MODEL

_SYSTEM_PROMPT_PATH = Path(__file__).with_name("system_prompt.md")


def _load_system_prompt() -> str:
    if _SYSTEM_PROMPT_PATH.is_file():
        return _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    return "You are a helpful assistant."


DEFAULT_SYSTEM_PROMPT = _load_system_prompt()

_CHANNEL_RE = re.compile(r"<\|channel\|>.*?(?=<\|channel|$)", re.DOTALL)
_THINK_BLOCK_RE = re.compile(r"<\|channel>thought\n.*?<channel\|>", re.DOTALL)

set_tracing_disabled(disabled=True)


def clean_agent_output(text: str, think: bool = False) -> str:
    """Strip Gemma-style channel markers and thinking blocks if think is disabled."""
    if not think:
        # Strip explicit thinking blocks first
        text = _THINK_BLOCK_RE.sub("", text)

    # Keep content after the last channel delimiter; if nothing follows,
    # walk back to earlier delimiters so we never return empty by accident.
    for marker in ("<channel|>", "<|channel|>", "<|channel>"):
        while marker in text:
            before, sep, after = text.rpartition(marker)
            if after.strip():
                text = after
                break
            text = before

    text = _CHANNEL_RE.sub("", text)
    text = text.replace("<|channel|>", "").replace("<|channel>", "").replace("<channel|>", "")
    text = re.sub(r"^\s*thought\s*\n?", "", text, flags=re.IGNORECASE)
    return text.strip()


def _strip_dict_thoughts(item: Dict[str, Any]) -> Dict[str, Any]:
    """Strip thinking content from an assistant message dict."""
    content = item.get("content")
    if isinstance(content, str):
        cleaned = clean_agent_output(content, think=False)
        if cleaned == content:
            return item
        return {**item, "content": cleaned or "(reasoning omitted)"}
    if isinstance(content, list):
        new_content: List[Any] = []
        modified = False
        for block in content:
            if isinstance(block, dict) and block.get("type") == "output_text":
                text = block.get("text", "")
                cleaned = clean_agent_output(text, think=False)
                if cleaned != text:
                    new_content.append({**block, "text": cleaned or "(reasoning omitted)"})
                    modified = True
                else:
                    new_content.append(block)
            else:
                new_content.append(block)
        if modified:
            return {**item, "content": new_content}
    return item


def _strip_model_thoughts(item: Any) -> Any:
    """Strip thinking content from an assistant message object, preserving type when possible."""
    content = getattr(item, "content", None)
    if isinstance(content, str):
        cleaned = clean_agent_output(content, think=False)
        if cleaned != content:
            # Try Pydantic model_copy (v2) or copy (v1) to preserve the original type
            model_copy = getattr(item, "model_copy", None) or getattr(item, "copy", None)
            if model_copy is not None:
                try:
                    return model_copy(update={"content": cleaned or "(reasoning omitted)"})
                except Exception:
                    pass
            # Fall back to in-place mutation
            try:
                item.content = cleaned or "(reasoning omitted)"
                return item
            except Exception:
                pass
    # Last resort: convert to dict
    if hasattr(item, "model_dump"):
        return _strip_dict_thoughts(item.model_dump())
    if hasattr(item, "to_dict"):
        return _strip_dict_thoughts(item.to_dict())
    return item


def strip_thoughts_from_history(items: List[Any]) -> List[Any]:
    """Return a copy of conversation items with assistant thinking stripped."""
    cleaned: List[Any] = []
    for item in items:
        is_assistant = False
        if isinstance(item, dict):
            is_assistant = item.get("role") == "assistant" or item.get("type") == "message"
        else:
            is_assistant = getattr(item, "role", None) == "assistant" or getattr(item, "type", None) == "message"
        if is_assistant:
            if isinstance(item, dict):
                item = _strip_dict_thoughts(item)
            else:
                item = _strip_model_thoughts(item)
        cleaned.append(item)
    return cleaned


def build_system_prompt(registry: SkillRegistry, base_prompt: str = DEFAULT_SYSTEM_PROMPT, think: bool = False) -> str:
    prefix = "<|think|>\n" if think else ""
    return f"{prefix}{base_prompt}\n\n{registry.catalog()}"


def _tool_arguments(args: Any) -> str:
    if args is None:
        return ""
    if isinstance(args, str):
        return args
    try:
        return json.dumps(args)
    except TypeError:
        return str(args)


def _extract_tool_call(item: ToolCallItem) -> Dict[str, Any]:
    raw = item.raw_item
    name = getattr(item, "title", None)
    arguments = ""
    call_id = None

    function = getattr(raw, "function", None)
    if function is not None:
        name = name or getattr(function, "name", None)
        arguments = getattr(function, "arguments", "") or ""
        call_id = getattr(raw, "id", None)
    else:
        name = name or getattr(raw, "name", None)
        arguments = _tool_arguments(getattr(raw, "arguments", None))
        call_id = getattr(raw, "call_id", None) or getattr(raw, "id", None)

    return {
        "id": call_id,
        "name": name,
        "arguments": arguments,
    }


def _extract_message_text(item: MessageOutputItem) -> str:
    raw = item.raw_item
    content = getattr(raw, "content", None)
    if isinstance(content, str):
        return content

    parts: List[str] = []
    if content:
        for block in content:
            text = getattr(block, "text", None)
            if text:
                parts.append(text)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
    return "".join(parts)


def serialize_agent_turns(new_items: List[Any]) -> List[Dict[str, Any]]:
    """Convert OpenAI Agents SDK run items into a compact UI-friendly trace."""
    tool_calls: List[Dict[str, Any]] = []
    tool_results: List[Dict[str, Any]] = []
    assistant_parts: List[str] = []

    for item in new_items:
        if isinstance(item, ToolCallItem):
            tool_calls.append(_extract_tool_call(item))
        elif isinstance(item, ToolCallOutputItem):
            tool_results.append(
                {
                    "name": getattr(item, "title", None),
                    "arguments": "",
                    "result": str(item.output or ""),
                }
            )
        elif isinstance(item, MessageOutputItem):
            text = _extract_message_text(item)
            if text:
                assistant_parts.append(text)

    if not tool_calls and not tool_results and not assistant_parts:
        return []

    return [
        {
            "turn": 1,
            "finish_reason": "stop",
            "content": "".join(assistant_parts) or None,
            "tool_calls": tool_calls,
            "tool_results": tool_results,
        }
    ]


serialize_cursor_messages = serialize_agent_turns

_PLAN_RE = re.compile(
    r"\b(I will|I'll|I plan to|I am going to|I need to|Let me|Next I will|I should|I could)\b",
    re.IGNORECASE,
)
_MAX_PLAN_RETRIES = 2


def _looks_like_plan(answer: str, new_items: List[Any]) -> bool:
    """Detect when the model described a plan instead of calling a tool."""
    if any(isinstance(item, ToolCallItem) for item in new_items):
        return False
    if len(answer.split()) < 4:
        return False
    return bool(_PLAN_RE.search(answer))


@dataclass
class AgentResult:
    """Final output from a completed agent run."""

    answer: str
    turns: List[Dict[str, Any]]
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    run_id: Optional[str] = None
    status: str = "finished"
    messages: List[Any] = field(default_factory=list)


class SkillAgentRunner:
    """Run a Gemma 4 agent via the OpenAI Agents SDK with skill function tools."""

    def __init__(
        self,
        *,
        skill_roots: Optional[List[Path]] = None,
        system_prompt: Optional[str] = None,
        cwd: Path = REPO_ROOT,
        verbose: bool = False,
        log_enabled: bool = True,
        log_stderr: bool = True,
        log_file: bool = True,
        trace_path: Path = TRACE_LOG,
        max_turns: int = 20,
    ) -> None:
        if not GEMMA4_API_KEY:
            raise RuntimeError("Set the GEMMA4_API_KEY environment variable.")

        self.cwd = cwd.resolve()
        self.verbose = verbose
        self.log_enabled = log_enabled
        self.log_stderr = log_stderr
        self.log_file = log_file
        self.trace_path = trace_path
        self.max_turns = max_turns
        self.model_name = GEMMA4_MODEL

        self._default_roots = tuple(skill_roots or default_skill_roots())
        self._system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self._client = AsyncOpenAI(
            api_key=GEMMA4_API_KEY,
            base_url=GEMMA4_BASE_URL,
        )
        self._model = OpenAIChatCompletionsModel(model=GEMMA4_MODEL, openai_client=self._client)
        self._current_task: Optional[str] = None
        self._think: bool = True
        self.agent: Optional[Agent] = None
        self.agent_id = "SkillAgent"
        self._build_agent()

    def _build_agent(self, task: Optional[str] = None, think: bool = True) -> None:
        if task:
            task_skills = REPO_ROOT / "tasks" / task / "skills"
            if task_skills.is_dir():
                # Task benchmarks: load only the task skill package (not repo .claude/.agents copies).
                roots = [task_skills]
            else:
                roots = list(self._default_roots)
        else:
            roots = list(self._default_roots)
        self.registry = SkillRegistry(*roots)
        instructions = build_system_prompt(self.registry, self._system_prompt, think=think)
        tools = build_tools(self.registry, base_path=str(self.cwd))
        if self.agent is not None:
            self.agent = self.agent.clone(
                instructions=instructions,
                tools=tools,
            )
        else:
            self.agent = Agent(
                name="SkillAgent",
                instructions=instructions,
                model=self._model,
                tools=tools,
                model_settings=ModelSettings(tool_choice="auto", include_usage=True),
            )
        self._current_task = task
        self._think = think

        SESSION_DB.parent.mkdir(parents=True, exist_ok=True)
        self._session_db = str(SESSION_DB)
        self._sessions: Dict[str, SQLiteSession] = {}
        self._lock = threading.Lock()

    def close(self) -> None:
        with self._lock:
            for session in self._sessions.values():
                try:
                    session.close()
                except Exception:  # noqa: BLE001
                    pass
            self._sessions.clear()

    def clear_session(self, session_id: str) -> None:
        with self._lock:
            session = self._sessions.pop(session_id, None)
        if session is not None:
            session.clear_session()
            session.close()

    def _get_session(self, session_id: str) -> SQLiteSession:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                session = SQLiteSession(session_id, db_path=self._session_db)
                self._sessions[session_id] = session
            return session

    def _trace_path(self) -> Path:
        if self._current_task:
            return REPO_ROOT / "tasks" / self._current_task / "logs" / "agent-core" / "agent_core_trace.jsonl"
        return self.trace_path

    def _make_logger(
        self,
        session_id: str,
        on_event: Optional[LogCallback] = None,
    ) -> AgentLogger:
        return AgentLogger(
            session_id=session_id,
            trace_path=self._trace_path(),
            stderr=self.log_enabled and self.log_stderr,
            file=self.log_enabled and self.log_file,
            on_event=on_event,
        )

    def _build_run_config(self, logger: AgentLogger) -> RunConfig:
        def call_model_input_filter(data: CallModelData[Any]) -> ModelInputData:
            # Log the raw history (with thinking) for observability
            logger.emit(
                "model_request",
                {
                    "agent": data.agent.name,
                    "instructions": data.model_data.instructions,
                    "input": serialize_model_input(list(data.model_data.input)),
                },
            )
            # Strip assistant thinking from the history sent to the model
            cleaned_input = strip_thoughts_from_history(list(data.model_data.input))
            return ModelInputData(
                input=cleaned_input,
                instructions=data.model_data.instructions,
            )

        return RunConfig(call_model_input_filter=call_model_input_filter)

    def _event_to_log(self, logger: AgentLogger, event: Any) -> List[Dict[str, Any]]:
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            delta = event.data.delta
            if not delta:
                return []
            logger.emit("model_delta", {"delta": delta})
            return [{"phase": "chat_delta", "data": {"delta": delta}}]

        if event.type != "run_item_stream_event":
            return []

        item = event.item
        if event.name == "tool_called" and isinstance(item, ToolCallItem):
            return logger.emit("tool_call", _extract_tool_call(item))

        if event.name == "tool_output" and isinstance(item, ToolCallOutputItem):
            return logger.emit(
                "tool_result",
                {
                    "name": getattr(item, "title", None),
                    "result": str(item.output or ""),
                },
            )

        if event.name == "message_output_created" and isinstance(item, MessageOutputItem):
            content = ItemHelpers.text_message_output(item)
            if not content:
                return []
            return logger.emit("assistant_message", {"content": content})

        return []

    async def run_stream(
        self,
        user_message: str,
        *,
        session_id: Optional[str] = None,
        task: Optional[str] = None,
        think: bool = True,
        on_event: Optional[LogCallback] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream log events in real time, ending with a run_complete event."""
        if task != self._current_task or think != self._think:
            self._build_agent(task, think=think)
        assert self.agent is not None

        active_session_id = session_id or "default"
        session = self._get_session(active_session_id)
        logger = self._make_logger(active_session_id, on_event=on_event)
        metrics_tracker = RunMetricsTracker()

        current_message = user_message
        result = None
        retries = 0

        while retries <= _MAX_PLAN_RETRIES:
            phase = "user_request" if retries == 0 else "correction"
            for event in logger.emit(phase, {"message": current_message}):
                yield event

            try:
                result = Runner.run_streamed(
                    self.agent,
                    current_message,
                    session=session,
                    max_turns=self.max_turns,
                    run_config=self._build_run_config(logger),
                )

                async for event in result.stream_events():
                    for log_event in self._event_to_log(logger, event):
                        yield log_event
            except Exception as exc:  # noqa: BLE001
                metrics = metrics_tracker.snapshot()
                for event in logger.emit("error", {"error": str(exc)}):
                    yield event
                for event in logger.finalize():
                    yield event
                for event in logger.emit("metrics", metrics):
                    yield event
                for event in logger.emit(
                    "run_complete",
                    {
                        "status": "error",
                        "answer": f"Error: agent run failed: {exc}",
                        "turns": [],
                        "agent_id": self.agent_id,
                        "run_id": None,
                        "metrics": metrics,
                    },
                ):
                    yield event
                return

            new_items = list(result.new_items)
            answer = clean_agent_output(str(result.final_output or ""), think=self._think)

            if _looks_like_plan(answer, new_items) and retries < _MAX_PLAN_RETRIES:
                for event in logger.emit("plan_detected", {"answer": answer, "retry": retries + 1}):
                    yield event
                current_message = "Do not describe your plan. Call the required tool immediately to get the answer."
                retries += 1
                continue

            break

        if result is None:
            metrics = metrics_tracker.snapshot()
            for event in logger.emit("error", {"error": "Agent run produced no result"}):
                yield event
            for event in logger.finalize():
                yield event
            for event in logger.emit("metrics", metrics):
                yield event
            for event in logger.emit(
                "run_complete",
                {
                    "status": "error",
                    "answer": "Error: agent run produced no result",
                    "turns": [],
                    "agent_id": self.agent_id,
                    "run_id": None,
                    "metrics": metrics,
                },
            ):
                yield event
            return

        turns = serialize_agent_turns(list(result.new_items))
        metrics = extract_run_metrics(result, metrics_tracker)

        run_id = None
        if result.raw_responses:
            run_id = getattr(result.raw_responses[-1], "id", None)

        if self.verbose:
            for turn in turns:
                print(f"--- Turn {turn['turn']} ---", file=sys.stderr)
                print(f"Assistant content: {turn['content']}", file=sys.stderr)
                print(f"Tool calls: {turn['tool_calls']}", file=sys.stderr)
                print(f"Tool results: {turn['tool_results']}", file=sys.stderr)

        for event in logger.finalize():
            yield event
        for event in logger.emit("metrics", metrics):
            yield event
        for event in logger.emit(
            "run_complete",
            {
                "status": "finished",
                "answer": answer,
                "turns": turns,
                "agent_id": self.agent_id,
                "run_id": run_id,
                "metrics": metrics,
            },
        ):
            yield event

    def run(
        self,
        user_message: str,
        *,
        session_id: Optional[str] = None,
        task: Optional[str] = None,
        think: bool = True,
        on_event: Optional[LogCallback] = None,
    ) -> AgentResult:
        """Send a message to the agent and return the final answer."""

        async def _consume() -> AgentResult:
            final_data: Optional[Dict[str, Any]] = None
            async for event in self.run_stream(
                user_message,
                session_id=session_id,
                task=task,
                think=think,
                on_event=on_event,
            ):
                if event.get("phase") == "run_complete":
                    final_data = event.get("data") or {}
            if final_data is None:
                return AgentResult(
                    answer="Error: agent run produced no result",
                    turns=[],
                    session_id=session_id or "default",
                    agent_id=self.agent_id,
                    status="error",
                )
            return AgentResult(
                answer=str(final_data.get("answer") or ""),
                turns=list(final_data.get("turns") or []),
                session_id=session_id or "default",
                agent_id=final_data.get("agent_id") or self.agent_id,
                run_id=final_data.get("run_id"),
                status=str(final_data.get("status") or "finished"),
            )

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_consume())

        # Already inside an active event loop (e.g., Jupyter, FastAPI).
        # Runner.run_sync also cannot be called from a running loop,
        # so nest_asyncio is required here.
        import nest_asyncio

        nest_asyncio.apply()
        return asyncio.run(_consume())


Gemma4AgentRunner = SkillAgentRunner
