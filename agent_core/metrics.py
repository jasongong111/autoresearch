"""Extract token usage and latency metrics from agent runs."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RunMetricsTracker:
    """Track wall-clock latency for a single agent run."""

    started_at: float = field(default_factory=time.perf_counter)

    def snapshot(self, usage: Any = None) -> Dict[str, Any]:
        latency_ms = round((time.perf_counter() - self.started_at) * 1000, 1)
        metrics: Dict[str, Any] = {
            "latency_ms": latency_ms,
        }
        metrics.update(_serialize_usage(usage))
        return metrics


def _serialize_usage(usage: Any) -> Dict[str, Any]:
    if usage is None:
        return {
            "requests": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "request_usage": [],
        }

    request_usage: List[Dict[str, Any]] = []
    entries = getattr(usage, "request_usage_entries", None) or []
    for entry in entries:
        request_usage.append(
            {
                "prompt_tokens": getattr(entry, "input_tokens", 0) or 0,
                "completion_tokens": getattr(entry, "output_tokens", 0) or 0,
                "total_tokens": getattr(entry, "total_tokens", 0) or 0,
            }
        )

    prompt_tokens = getattr(usage, "input_tokens", 0) or 0
    completion_tokens = getattr(usage, "output_tokens", 0) or 0
    total_tokens = getattr(usage, "total_tokens", 0) or 0

    return {
        "requests": getattr(usage, "requests", len(request_usage) or 0) or 0,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "request_usage": request_usage,
    }


def extract_run_metrics(result: Any, tracker: RunMetricsTracker) -> Dict[str, Any]:
    usage = None
    # Try multiple known paths for usage data across SDK versions and providers.
    if result is not None:
        usage = getattr(getattr(result, "context_wrapper", None), "usage", None)
        if usage is None:
            usage = getattr(result, "usage", None)
        if usage is None:
            # Last raw response sometimes carries usage metadata.
            raw_responses = getattr(result, "raw_responses", None) or []
            if raw_responses:
                usage = getattr(raw_responses[-1], "usage", None)
    return tracker.snapshot(usage=usage)
