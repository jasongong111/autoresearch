import { useMemo, useState } from "react";
import type { TraceArtifact, TraceEvent, TraceStream } from "../types";

interface Props {
  events: TraceEvent[];
  artifacts: TraceArtifact[];
  command?: string;
  traceName?: string;
  tracePath?: string;
  streams?: TraceStream[];
}

function levelClass(level: string): string {
  if (level === "success") return "success";
  if (level === "failure") return "failure";
  if (level === "warning") return "warning";
  return "info";
}

function formatTs(ts: string): string {
  if (!ts) return "";
  try {
    const d = new Date(ts);
    if (Number.isNaN(d.getTime())) return ts;
    return d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch {
    return ts;
  }
}

function formatJsonl(content: string): string {
  return content
    .split("\n")
    .filter((line) => line.trim())
    .map((line) => {
      try {
        return JSON.stringify(JSON.parse(line), null, 2);
      } catch {
        return line;
      }
    })
    .join("\n\n");
}

const BASE_EVENT_KEYS = new Set([
  "ts",
  "phase",
  "message",
  "iteration",
  "round",
  "detail",
  "level",
]);

function formatValue(value: unknown): string {
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function eventPayloads(event: TraceEvent): [string, unknown][] {
  return Object.entries(event).filter(([key, value]) => {
    if (BASE_EVENT_KEYS.has(key)) return false;
    return value !== undefined && value !== null && value !== "";
  });
}

export default function AgentTrace({
  events,
  artifacts,
  command,
  traceName = "Agent trace",
  tracePath = ".autoresearch/trace.jsonl",
  streams,
}: Props) {
  const availableStreams = useMemo(
    () => streams?.filter((stream) => stream.events.length > 0) ?? [],
    [streams]
  );
  const [selectedStreamId, setSelectedStreamId] = useState<string | null>(
    availableStreams[0]?.id ?? null
  );
  const [selectedArtifact, setSelectedArtifact] = useState<string | null>(
    artifacts[0]?.name ?? null
  );
  const [filterIteration, setFilterIteration] = useState<number | "all">("all");
  const activeStream =
    availableStreams.find((stream) => stream.id === selectedStreamId) ?? availableStreams[0];
  const activeEvents = activeStream?.events ?? events;
  const activeTraceName = activeStream?.title ?? traceName;
  const activeTracePath = activeStream?.path ?? tracePath;

  const filteredEvents = useMemo(() => {
    if (filterIteration === "all") return activeEvents;
    return activeEvents.filter(
      (e) => e.iteration === filterIteration || e.round === filterIteration
    );
  }, [activeEvents, filterIteration]);

  const indexOptions = useMemo(() => {
    const nums = new Set<number>();
    activeEvents.forEach((e) => {
      if (e.iteration != null) nums.add(e.iteration);
      if (e.round != null) nums.add(e.round);
    });
    return [...nums].sort((a, b) => a - b);
  }, [activeEvents]);

  const activeArtifact = artifacts.find((a) => a.name === selectedArtifact) ?? artifacts[0];

  const hasEvents = activeEvents.length > 0;
  const hasArtifacts = artifacts.length > 0;

  if (!hasEvents && !hasArtifacts) {
    return (
      <p className="empty">
        No {traceName.toLowerCase()} yet. During a run, append events to{" "}
        <code>{activeTracePath}</code> or use subcommands that write trace artifacts
        (predict, reason, debug, etc.).
      </p>
    );
  }

  return (
    <div className="trace-panel">
      {hasEvents && (
        <div className="trace-section">
          <div className="trace-toolbar">
            <span className="trace-toolbar-label">Live {activeTraceName.toLowerCase()}</span>
            {availableStreams.length > 1 && (
              <select
                className="select"
                value={activeStream?.id ?? ""}
                onChange={(e) => {
                  setSelectedStreamId(e.target.value);
                  setFilterIteration("all");
                }}
              >
                {availableStreams.map((stream) => (
                  <option key={stream.id} value={stream.id}>
                    {stream.title} ({stream.events.length})
                  </option>
                ))}
              </select>
            )}
            {indexOptions.length > 0 && (
              <select
                className="select"
                value={filterIteration === "all" ? "all" : String(filterIteration)}
                onChange={(e) =>
                  setFilterIteration(e.target.value === "all" ? "all" : Number(e.target.value))
                }
              >
                <option value="all">All {command === "predict" || command === "reason" ? "rounds" : "iterations"}</option>
                {indexOptions.map((n) => (
                  <option key={n} value={n}>
                    {command === "predict" || command === "reason" ? "Round" : "Iteration"} {n}
                  </option>
                ))}
              </select>
            )}
          </div>
          <ol className="trace-list">
            {filteredEvents.map((e, i) => (
              <li key={`${e.ts}-${i}`} className={levelClass(e.level)}>
                <div className="trace-meta">
                  {e.ts && <time>{formatTs(e.ts)}</time>}
                  <span className="trace-phase">{e.phase}</span>
                  {(e.iteration != null || e.round != null) && (
                    <span className="trace-index">
                      {e.round != null ? `R${e.round}` : `#${e.iteration}`}
                    </span>
                  )}
                </div>
                <div className="trace-message">{e.message}</div>
                {e.detail && <div className="trace-detail">{e.detail}</div>}
                {eventPayloads(e).map(([key, value]) => (
                  <details className="trace-payload" key={key}>
                    <summary>{key}</summary>
                    <pre>{formatValue(value)}</pre>
                  </details>
                ))}
              </li>
            ))}
          </ol>
        </div>
      )}

      {hasArtifacts && (
        <div className="trace-section">
          <div className="trace-toolbar">
            <span className="trace-toolbar-label">Trace documents</span>
            <select
              className="select"
              value={activeArtifact?.name ?? ""}
              onChange={(e) => setSelectedArtifact(e.target.value)}
            >
              {artifacts.map((a) => (
                <option key={a.name} value={a.name}>
                  {a.title}
                </option>
              ))}
            </select>
          </div>
          {activeArtifact && (
            <pre className="trace-doc">
              {activeArtifact.kind === "jsonl"
                ? formatJsonl(activeArtifact.content)
                : activeArtifact.content}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
