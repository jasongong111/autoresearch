"""Agent trace parsing — live JSONL events and run-directory artifacts."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

TRACE_PATH = ".autoresearch/trace.jsonl"

# Markdown / JSONL artifacts that carry agent reasoning traces per command folder.
RUN_TRACE_ARTIFACTS: Dict[str, str] = {
    "persona-debates.md": "Persona debates",
    "judge-transcripts.md": "Judge transcripts",
    "lineage.md": "Lineage",
    "reason-lineage.jsonl": "Lineage (JSONL)",
    "findings.md": "Findings",
    "eliminated.md": "Eliminated hypotheses",
    "contradictions.md": "Contradictions",
    "hidden-assumptions.md": "Hidden assumptions",
    "overview.md": "Overview",
    "hypothesis-queue.md": "Hypothesis queue",
    "scout-context.md": "Scout context",
    "summary.md": "Summary",
}


@dataclass
class TraceEvent:
    ts: str
    phase: str
    message: str
    iteration: Optional[int] = None
    round: Optional[int] = None
    detail: Optional[str] = None
    level: str = "info"

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "ts": self.ts,
            "phase": self.phase,
            "message": self.message,
            "level": self.level,
        }
        if self.iteration is not None:
            out["iteration"] = self.iteration
        if self.round is not None:
            out["round"] = self.round
        if self.detail:
            out["detail"] = self.detail
        return out


@dataclass
class TraceArtifact:
    name: str
    title: str
    content: str
    last_modified: float
    kind: str = "markdown"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "title": self.title,
            "content": self.content,
            "lastModified": self.last_modified,
            "kind": self.kind,
        }


def trace_file_path(project_root: Path) -> Path:
    return project_root / TRACE_PATH


def parse_trace_jsonl(path: Path) -> List[TraceEvent]:
    if not path.is_file():
        return []
    events: List[TraceEvent] = []
    for obj in parse_trace_objects(path):
        message = str(obj.get("message") or obj.get("msg") or "").strip()
        phase = str(obj.get("phase") or "info").strip()
        if not message:
            continue
        iteration = _optional_int(obj.get("iteration"))
        round_num = _optional_int(obj.get("round"))
        events.append(
            TraceEvent(
                ts=str(obj.get("ts") or obj.get("timestamp") or ""),
                phase=phase,
                message=message,
                iteration=iteration,
                round=round_num,
                detail=_optional_str(obj.get("detail")),
                level=str(obj.get("level") or "info").lower(),
            )
        )
    return events


def parse_trace_objects(path: Path) -> List[Dict[str, Any]]:
    """Read trace JSONL as raw objects, ignoring malformed lines."""
    if not path.is_file():
        return []
    objects: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            objects.append(obj)
    return objects


def parse_trace_analytics(path: Path) -> Dict[str, Any]:
    """Aggregate richer trace events into dashboard analytics."""
    return compute_trace_analytics(parse_trace_objects(path))


def compute_trace_analytics(objects: List[Dict[str, Any]]) -> Dict[str, Any]:
    traces = [o for o in objects if _event_type(o) == "trace"]
    observations = [o for o in objects if _event_type(o) == "observation"]
    scores = [o for o in objects if _event_type(o) == "score"]
    generations = [o for o in observations if _is_generation(o)]

    model_costs: Dict[str, Dict[str, float]] = defaultdict(lambda: {"tokens": 0.0, "costUsd": 0.0})
    cost_by_user: Dict[str, float] = defaultdict(float)
    trace_count_by_user: Dict[str, int] = defaultdict(int)
    trace_names: Dict[str, int] = defaultdict(int)

    for trace in traces:
        name = _name(trace)
        trace_names[name] += 1
        trace_count_by_user[_user(trace)] += 1

    for obs in generations:
        model = _model(obs)
        tokens = _usage_total(obs)
        cost = _cost_total(obs)
        model_costs[model]["tokens"] += tokens
        model_costs[model]["costUsd"] += cost
        cost_by_user[_user(obs)] += cost

    score_summary = _score_summary(scores)

    return {
        "traces": {
            "total": len(traces),
            "byName": _count_rows(trace_names, "name", "count"),
        },
        "modelCosts": {
            "totalCostUsd": _round(sum(v["costUsd"] for v in model_costs.values())),
            "byModel": _model_cost_rows(model_costs),
        },
        "scores": {
            "total": len(scores),
            "summary": score_summary,
        },
        "timeSeries": {
            "traceObservationByLevel": _trace_observation_series(traces, observations),
            "observationsByLevel": _observation_level_series(observations),
        },
        "modelUsage": _model_usage(generations),
        "userConsumption": {
            "costByUser": _user_cost_rows(cost_by_user),
            "traceCountByUser": _user_trace_rows(trace_count_by_user),
        },
        "scoreTimeSeries": _score_time_series(scores),
        "latencies": {
            "trace": _latency_rows(traces),
            "generation": _latency_rows(generations),
            "observation": _latency_rows(observations),
        },
        "modelLatencies": {
            "series": _model_latency_series(generations),
        },
        "scoreAnalytics": _score_analytics(scores),
    }


def discover_run_artifacts(project_root: Path, run_id: str) -> List[TraceArtifact]:
    """Find trace markdown/jsonl files in the same directory as a run TSV."""
    run_path = (project_root / run_id).resolve()
    if not run_path.is_file():
        return []
    run_dir = run_path.parent
    artifacts: List[TraceArtifact] = []
    for filename, title in RUN_TRACE_ARTIFACTS.items():
        path = run_dir / filename
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        kind = "jsonl" if filename.endswith(".jsonl") else "markdown"
        artifacts.append(
            TraceArtifact(
                name=filename,
                title=title,
                content=content,
                last_modified=path.stat().st_mtime,
                kind=kind,
            )
        )
    artifacts.sort(key=lambda a: a.name)
    return artifacts


def _event_type(obj: Dict[str, Any]) -> str:
    return str(obj.get("type") or obj.get("eventType") or "").strip().lower()


def _name(obj: Dict[str, Any]) -> str:
    return str(obj.get("name") or obj.get("phase") or "unknown").strip() or "unknown"


def _user(obj: Dict[str, Any]) -> str:
    return str(obj.get("userId") or obj.get("user") or "unknown").strip() or "unknown"


def _model(obj: Dict[str, Any]) -> str:
    return str(obj.get("model") or obj.get("modelName") or "unknown").strip() or "unknown"


def _level(obj: Dict[str, Any]) -> str:
    return str(obj.get("level") or "DEFAULT").strip().upper() or "DEFAULT"


def _is_generation(obj: Dict[str, Any]) -> bool:
    kind = str(obj.get("observationType") or obj.get("kind") or obj.get("typeName") or "").lower()
    return kind in {"generation", "completion", "chat", "llm"}


def _as_number(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _nested_number(obj: Dict[str, Any], key: str, nested: str) -> float:
    direct = _as_number(obj.get(key))
    if direct is not None:
        return direct
    values = obj.get(nested)
    if isinstance(values, dict):
        total = _as_number(values.get("total"))
        if total is not None:
            return total
        return sum(_as_number(v) or 0.0 for v in values.values())
    return 0.0


def _usage_total(obj: Dict[str, Any]) -> float:
    return _nested_number(obj, "usage", "usage")


def _cost_total(obj: Dict[str, Any]) -> float:
    return _nested_number(obj, "cost", "cost")


def _detail_items(obj: Dict[str, Any], key: str) -> Dict[str, float]:
    values = obj.get(key)
    if not isinstance(values, dict):
        return {}
    return {
        str(k): float(v)
        for k, v in ((k, _as_number(v)) for k, v in values.items())
        if v is not None and str(k) != "total"
    }


def _round(value: float) -> float:
    return round(value, 6)


def _bucket(ts: Any) -> str:
    raw = str(ts or "").strip()
    if not raw:
        return "unknown"
    normalized = raw.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
        return dt.isoformat().replace("+00:00", "Z")
    except ValueError:
        return raw[:13] if len(raw) >= 13 else raw


def _count_rows(values: Dict[str, int], key_name: str, value_name: str) -> List[Dict[str, Any]]:
    return [
        {key_name: key, value_name: count}
        for key, count in sorted(values.items(), key=lambda item: (-item[1], item[0]))
    ]


def _model_cost_rows(values: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
    return [
        {"model": model, "tokens": int(stats["tokens"]), "costUsd": _round(stats["costUsd"])}
        for model, stats in sorted(values.items(), key=lambda item: (-item[1]["costUsd"], item[0]))
    ]


def _score_key(score: Dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(score.get("name") or "unknown"),
        str(score.get("source") or "unknown"),
        str(score.get("dataType") or score.get("valueType") or "UNKNOWN").upper(),
    )


def _score_summary(scores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[tuple[str, str, str], List[Any]] = defaultdict(list)
    for score in scores:
        grouped[_score_key(score)].append(score.get("value"))

    rows: List[Dict[str, Any]] = []
    for (name, source, data_type), values in grouped.items():
        numeric = [_as_number(v) for v in values]
        numeric_values = [v for v in numeric if v is not None]
        rows.append(
            {
                "name": name,
                "source": source,
                "dataType": data_type,
                "count": len(values),
                "average": _round(sum(numeric_values) / len(numeric_values)) if numeric_values else None,
                "zeros": sum(1 for v in numeric_values if v == 0),
                "ones": sum(1 for v in numeric_values if v == 1),
            }
        )
    rows.sort(key=lambda row: (-row["count"], row["name"], row["source"], row["dataType"]))
    return rows


def _trace_observation_series(
    traces: List[Dict[str, Any]],
    observations: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    buckets: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"traceCount": 0, "observationsByLevel": defaultdict(int)})
    for trace in traces:
        buckets[_bucket(trace.get("ts") or trace.get("timestamp"))]["traceCount"] += 1
    for obs in observations:
        buckets[_bucket(obs.get("ts") or obs.get("timestamp"))]["observationsByLevel"][_level(obs)] += 1
    return [
        {
            "bucket": bucket,
            "traceCount": values["traceCount"],
            "observationCount": sum(values["observationsByLevel"].values()),
            "observationsByLevel": dict(sorted(values["observationsByLevel"].items())),
        }
        for bucket, values in sorted(buckets.items())
    ]


def _observation_level_series(observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    buckets: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for obs in observations:
        buckets[_bucket(obs.get("ts") or obs.get("timestamp"))][_level(obs)] += 1
    return [
        {"bucket": bucket, "observationsByLevel": dict(sorted(levels.items()))}
        for bucket, levels in sorted(buckets.items())
    ]


def _series_row(bucket: str, name_key: str, name: str, value_key: str, value: float) -> Dict[str, Any]:
    return {"bucket": bucket, name_key: name, value_key: _round(value)}


def _model_usage(generations: List[Dict[str, Any]]) -> Dict[str, Any]:
    models = sorted({_model(obs) for obs in generations})
    cost_by_model: Dict[tuple[str, str], float] = defaultdict(float)
    usage_by_model: Dict[tuple[str, str], float] = defaultdict(float)
    cost_by_type: Dict[tuple[str, str], float] = defaultdict(float)
    usage_by_type: Dict[tuple[str, str], float] = defaultdict(float)

    for obs in generations:
        bucket = _bucket(obs.get("ts") or obs.get("timestamp"))
        model = _model(obs)
        cost_by_model[(bucket, model)] += _cost_total(obs)
        usage_by_model[(bucket, model)] += _usage_total(obs)
        for cost_type, value in _detail_items(obs, "cost").items():
            cost_by_type[(bucket, cost_type)] += value
        for usage_type, value in _detail_items(obs, "usage").items():
            usage_by_type[(bucket, usage_type)] += value

    return {
        "models": models,
        "costByModel": [
            _series_row(bucket, "model", model, "costUsd", value)
            for (bucket, model), value in sorted(cost_by_model.items())
        ],
        "costByType": [
            _series_row(bucket, "costType", cost_type, "costUsd", value)
            for (bucket, cost_type), value in sorted(cost_by_type.items())
        ],
        "usageByModel": [
            _series_row(bucket, "model", model, "tokens", value)
            for (bucket, model), value in sorted(usage_by_model.items())
        ],
        "usageByType": [
            _series_row(bucket, "usageType", usage_type, "tokens", value)
            for (bucket, usage_type), value in sorted(usage_by_type.items())
        ],
    }


def _user_cost_rows(values: Dict[str, float]) -> List[Dict[str, Any]]:
    return [
        {"user": user, "totalCostUsd": _round(cost)}
        for user, cost in sorted(values.items(), key=lambda item: (-item[1], item[0]))
    ]


def _user_trace_rows(values: Dict[str, int]) -> List[Dict[str, Any]]:
    return [
        {"user": user, "traceCount": count}
        for user, count in sorted(values.items(), key=lambda item: (-item[1], item[0]))
    ]


def _score_time_series(scores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[tuple[str, str, str], List[Dict[str, Any]]] = defaultdict(list)
    for score in scores:
        grouped[_score_key(score)].append(score)
    rows: List[Dict[str, Any]] = []
    for (name, source, data_type), items in grouped.items():
        numeric_values: List[float] = []
        for score in sorted(items, key=lambda s: str(s.get("ts") or s.get("timestamp") or "")):
            value = _as_number(score.get("value"))
            if value is None:
                continue
            numeric_values.append(value)
            window = numeric_values[-5:]
            rows.append(
                {
                    "bucket": _bucket(score.get("ts") or score.get("timestamp")),
                    "name": name,
                    "source": source,
                    "dataType": data_type,
                    "movingAverage": _round(sum(window) / len(window)),
                }
            )
    return rows


def _latency_ms(obj: Dict[str, Any]) -> Optional[float]:
    for key in ("latencyMs", "durationMs", "latency_ms", "duration_ms"):
        value = _as_number(obj.get(key))
        if value is not None:
            return value
    start = obj.get("startTime") or obj.get("start_time")
    end = obj.get("endTime") or obj.get("end_time")
    if not start or not end:
        return None
    try:
        start_dt = datetime.fromisoformat(str(start).replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(str(end).replace("Z", "+00:00"))
    except ValueError:
        return None
    return max(0.0, (end_dt - start_dt).total_seconds() * 1000)


def _percentile(values: List[float], percentile: float) -> Optional[float]:
    if not values:
        return None
    sorted_values = sorted(values)
    index = max(0, min(len(sorted_values) - 1, math.ceil(percentile * len(sorted_values)) - 1))
    return _round(sorted_values[index])


def _percentiles(values: List[float], include_p75: bool = False) -> Dict[str, Optional[float]]:
    out: Dict[str, Optional[float]] = {
        "p50Ms": _percentile(values, 0.50),
        "p90Ms": _percentile(values, 0.90),
        "p95Ms": _percentile(values, 0.95),
        "p99Ms": _percentile(values, 0.99),
    }
    if include_p75:
        out = {"p50Ms": out["p50Ms"], "p75Ms": _percentile(values, 0.75), **{k: v for k, v in out.items() if k != "p50Ms"}}
    return out


def _latency_rows(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[float]] = defaultdict(list)
    for event in events:
        latency = _latency_ms(event)
        if latency is not None:
            grouped[_name(event)].append(latency)
    return [
        {"name": name, **_percentiles(values)}
        for name, values in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))
    ]


def _model_latency_series(generations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[tuple[str, str], List[float]] = defaultdict(list)
    for obs in generations:
        latency = _latency_ms(obs)
        if latency is not None:
            grouped[(_bucket(obs.get("ts") or obs.get("timestamp")), _model(obs))].append(latency)
    return [
        {"bucket": bucket, "model": model, **_percentiles(values, include_p75=True)}
        for (bucket, model), values in sorted(grouped.items())
    ]


def _score_id(name: str, source: str, data_type: str) -> str:
    return f"{name}|{source}|{data_type}"


def _score_analytics(scores: List[Dict[str, Any]]) -> Dict[str, Any]:
    grouped: Dict[tuple[str, str, str], List[Dict[str, Any]]] = defaultdict(list)
    for score in scores:
        grouped[_score_key(score)].append(score)

    analytics: Dict[str, Any] = {}
    for (name, source, data_type), items in grouped.items():
        numeric_values = [_as_number(score.get("value")) for score in items]
        numeric_values = [v for v in numeric_values if v is not None]
        categorical: Dict[str, int] = defaultdict(int)
        categorical_by_bucket: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for score in items:
            value = score.get("value")
            label = str(value)
            categorical[label] += 1
            categorical_by_bucket[_bucket(score.get("ts") or score.get("timestamp"))][label] += 1

        histogram = _histogram(numeric_values) if numeric_values else []
        analytics[_score_id(name, source, data_type)] = {
            "name": name,
            "source": source,
            "dataType": data_type,
            "histogram": histogram,
            "categoricalBreakdown": _count_rows(categorical, "category", "count"),
            "movingAverage": [
                row for row in _score_time_series(items)
                if row["name"] == name and row["source"] == source and row["dataType"] == data_type
            ],
            "categoricalOverTime": [
                {"bucket": bucket, "counts": dict(sorted(counts.items()))}
                for bucket, counts in sorted(categorical_by_bucket.items())
            ],
        }
    return analytics


def _histogram(values: List[float]) -> List[Dict[str, Any]]:
    counts: Dict[str, int] = defaultdict(int)
    for value in values:
        label = str(int(value)) if float(value).is_integer() else str(_round(value))
        counts[label] += 1
    return [
        {"bucket": bucket, "count": count}
        for bucket, count in sorted(counts.items(), key=lambda item: float(item[0]))
    ]


def _optional_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    return s or None
