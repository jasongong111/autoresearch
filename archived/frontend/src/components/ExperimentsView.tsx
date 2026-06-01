import { useMemo, useState } from "react";
import type { ExperimentRecord } from "../types";

interface Props {
  experiments: ExperimentRecord[];
}

function statusClass(status: string): string {
  const s = status.toLowerCase();
  if (s === "keep" || s === "keep (reworked)") return "success";
  if (s === "discard") return "failure";
  if (s === "crash" || s === "metric-error") return "warning";
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

function formatJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

export default function ExperimentsView({ experiments }: Props) {
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const statuses = useMemo(() => {
    const set = new Set(experiments.map((e) => e.status));
    return ["all", ...Array.from(set).sort()];
  }, [experiments]);

  const filtered = useMemo(() => {
    if (filterStatus === "all") return experiments;
    return experiments.filter((e) => e.status === filterStatus);
  }, [experiments, filterStatus]);

  if (experiments.length === 0) {
    return (
      <p className="empty">
        No experiments logged yet. The agent writes to{" "}
        <code>.autoresearch/experiment.jsonl</code> at the end of each iteration.
      </p>
    );
  }

  return (
    <div className="experiments-panel">
      <div className="trace-toolbar">
        <span className="trace-toolbar-label">Experiment records</span>
        <select
          className="select"
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
        >
          {statuses.map((s) => (
            <option key={s} value={s}>
              {s === "all" ? "All statuses" : s}
            </option>
          ))}
        </select>
        <span className="badge outline">{filtered.length} records</span>
      </div>

      <ol className="trace-list">
        {filtered.map((e) => {
          const isExpanded = expandedId === e.iteration;
          return (
            <li key={e.iteration} className={statusClass(e.status)}>
              <div className="trace-meta">
                {e.timestamp && <time>{formatTs(e.timestamp)}</time>}
                <span className="trace-phase">{e.status}</span>
                <span className="trace-index">#{e.iteration}</span>
                {e.commit && e.commit !== "-" && (
                  <code className="trace-commit">{e.commit}</code>
                )}
              </div>
              <div className="trace-message">{e.description}</div>
              {e.metric != null && (
                <div className="trace-detail">
                  metric: {e.metric}
                  {e.delta != null && (
                    <span className={e.delta >= 0 ? "delta-positive" : "delta-negative"}>
                      {" "}
                      ({e.delta >= 0 ? "+" : ""}
                      {e.delta})
                    </span>
                  )}{" "}
                  · guard: {e.guard}
                </div>
              )}
              {(e.hypothesis || e.filesModified?.length || e.toolsUsed?.length) && (
                <button
                  type="button"
                  className="btn btn-small"
                  onClick={() => setExpandedId(isExpanded ? null : e.iteration)}
                >
                  {isExpanded ? "Collapse" : "Details"}
                </button>
              )}
              {isExpanded && (
                <div className="trace-payload-panel">
                  {e.hypothesis && (
                    <details open>
                      <summary>Hypothesis</summary>
                      <p>{e.hypothesis}</p>
                    </details>
                  )}
                  {e.filesRead && e.filesRead.length > 0 && (
                    <details open>
                      <summary>Files read ({e.filesRead.length})</summary>
                      <ul>
                        {e.filesRead.map((f) => (
                          <li key={f}>
                            <code>{f}</code>
                          </li>
                        ))}
                      </ul>
                    </details>
                  )}
                  {e.filesModified && e.filesModified.length > 0 && (
                    <details open>
                      <summary>Files modified ({e.filesModified.length})</summary>
                      <ul>
                        {e.filesModified.map((f) => (
                          <li key={f}>
                            <code>{f}</code>
                          </li>
                        ))}
                      </ul>
                    </details>
                  )}
                  {e.toolsUsed && e.toolsUsed.length > 0 && (
                    <details open>
                      <summary>Tools used ({e.toolsUsed.length})</summary>
                      <ul className="tool-list">
                        {e.toolsUsed.map((t, i) => (
                          <li key={i}>
                            <strong>{t.name}</strong>
                            <pre>{formatJson(t.input)}</pre>
                          </li>
                        ))}
                      </ul>
                    </details>
                  )}
                  {e.verifyOutput && (
                    <details>
                      <summary>Verify output</summary>
                      <pre className="trace-output">{e.verifyOutput}</pre>
                    </details>
                  )}
                  {e.guardOutput && (
                    <details>
                      <summary>Guard output</summary>
                      <pre className="trace-output">{e.guardOutput}</pre>
                    </details>
                  )}
                  {e.durationMs != null && (
                    <div className="trace-detail">Duration: {e.durationMs}ms</div>
                  )}
                </div>
              )}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
