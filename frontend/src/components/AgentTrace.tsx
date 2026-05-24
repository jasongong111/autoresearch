import { useMemo, useState } from "react";
import type { TraceArtifact, TraceEvent } from "./types";

interface Props {
  events: TraceEvent[];
  artifacts: TraceArtifact[];
  command?: string;
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

export default function AgentTrace({ events, artifacts, command }: Props) {
  const [selectedArtifact, setSelectedArtifact] = useState<string | null>(
    artifacts[0]?.name ?? null
  );
  const [filterIteration, setFilterIteration] = useState<number | "all">("all");

  const filteredEvents = useMemo(() => {
    if (filterIteration === "all") return events;
    return events.filter(
      (e) => e.iteration === filterIteration || e.round === filterIteration
    );
  }, [events, filterIteration]);

  const indexOptions = useMemo(() => {
    const nums = new Set<number>();
    events.forEach((e) => {
      if (e.iteration != null) nums.add(e.iteration);
      if (e.round != null) nums.add(e.round);
    });
    return [...nums].sort((a, b) => a - b);
  }, [events]);

  const activeArtifact = artifacts.find((a) => a.name === selectedArtifact) ?? artifacts[0];

  const hasEvents = events.length > 0;
  const hasArtifacts = artifacts.length > 0;

  if (!hasEvents && !hasArtifacts) {
    return (
      <p className="empty">
        No agent trace yet. During a run, append events to{" "}
        <code>.autoresearch/trace.jsonl</code> or use subcommands that write trace artifacts
        (predict, reason, debug, etc.).
      </p>
    );
  }

  return (
    <div className="trace-panel">
      {hasEvents && (
        <div className="trace-section">
          <div className="trace-toolbar">
            <span className="trace-toolbar-label">Live trace</span>
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
