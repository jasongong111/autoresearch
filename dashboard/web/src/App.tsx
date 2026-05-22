import { useCallback, useEffect, useState } from "react";
import {
  fetchGitCommits,
  fetchHealth,
  fetchIterations,
  fetchRun,
  fetchRunArtifacts,
  fetchRuns,
  fetchSummary,
  fetchTrace,
  subscribeEvents,
} from "./api";
import AgentTrace from "./AgentTrace";
import GitTimeline from "./GitTimeline";
import IterationTable from "./IterationTable";
import MetricChart from "./MetricChart";
import type { GitCommit, Iteration, Run, Session, Summary, TraceArtifact, TraceEvent } from "./types";

export default function App() {
  const [project, setProject] = useState("");
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [iterations, setIterations] = useState<Iteration[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [commits, setCommits] = useState<GitCommit[]>([]);
  const [traceEvents, setTraceEvents] = useState<TraceEvent[]>([]);
  const [artifacts, setArtifacts] = useState<TraceArtifact[]>([]);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadRunData = useCallback(async (runId: string) => {
    const [iters, sum, runDetail, trace, arts] = await Promise.all([
      fetchIterations(runId),
      fetchSummary(runId),
      fetchRun(runId),
      fetchTrace(),
      fetchRunArtifacts(runId),
    ]);
    setIterations(iters);
    setSummary(sum);
    setSession(runDetail.session);
    setTraceEvents(trace);
    setArtifacts(arts);
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [health, runsData, gitData] = await Promise.all([
        fetchHealth(),
        fetchRuns(),
        fetchGitCommits(),
      ]);
      setProject(health.project);
      setRuns(runsData.runs);
      setCommits(gitData);
      const active = runsData.activeRunId ?? runsData.runs[0]?.runId ?? null;
      const runId = selectedRunId && runsData.runs.some((r) => r.runId === selectedRunId)
        ? selectedRunId
        : active;
      if (runId) {
        setSelectedRunId(runId);
        await loadRunData(runId);
      }
    } finally {
      setLoading(false);
    }
  }, [selectedRunId, loadRunData]);

  useEffect(() => {
    refresh();
  }, []);

  useEffect(() => {
    const unsub = subscribeEvents((event) => {
      if (event.type === "connected") {
        setConnected(true);
        return;
      }
      if (event.type === "disconnected") {
        setConnected(false);
        return;
      }
      setConnected(true);
      if (event.type === "run_updated" && event.runId) {
        if (event.runId === selectedRunId) {
          loadRunData(event.runId);
        }
        fetchRuns().then((d) => setRuns(d.runs));
      }
      if (event.type === "git_updated") {
        fetchGitCommits().then(setCommits);
      }
      if (event.type === "trace_updated") {
        fetchTrace().then(setTraceEvents);
        if (selectedRunId && (!event.runId || event.runId === selectedRunId)) {
          fetchRunArtifacts(selectedRunId).then(setArtifacts);
        }
      }
    });
    setConnected(true);
    return unsub;
  }, [selectedRunId, loadRunData]);

  const handleRunChange = async (runId: string) => {
    setSelectedRunId(runId);
    await loadRunData(runId);
  };

  const selectedRun = runs.find((r) => r.runId === selectedRunId);
  const groupedRuns = runs.reduce<Record<string, Run[]>>((acc, r) => {
    (acc[r.command] ??= []).push(r);
    return acc;
  }, {});

  return (
    <div className="app">
      <header className="header">
        <h1>Autoresearch Dashboard</h1>
        <span className="project" title={project}>
          {project || "—"}
        </span>
        <span>
          <span className={`status-dot ${connected ? "connected" : "disconnected"}`} />
          {connected ? "Live" : "Reconnecting…"}
        </span>
        <button type="button" onClick={() => refresh()}>
          Refresh
        </button>
        <select
          value={selectedRunId ?? ""}
          onChange={(e) => handleRunChange(e.target.value)}
          disabled={runs.length === 0}
        >
          {Object.entries(groupedRuns).map(([cmd, cmdRuns]) => (
            <optgroup key={cmd} label={cmd}>
              {cmdRuns.map((r) => (
                <option key={r.runId} value={r.runId}>
                  {r.runId} ({r.rowCount} rows)
                </option>
              ))}
            </optgroup>
          ))}
        </select>
      </header>

      <div className="main">
        <div className="content">
          {loading && !selectedRun ? (
            <p className="empty">Loading…</p>
          ) : !selectedRun ? (
            <p className="empty">No autoresearch runs detected. Start /autoresearch in the watched project.</p>
          ) : (
            <>
              {session?.goal && (
                <div className="cards" style={{ marginBottom: 12 }}>
                  <div className="card" style={{ gridColumn: "1 / -1" }}>
                    <div className="label">Goal</div>
                    <div className="value" style={{ fontSize: "0.95rem" }}>
                      {session.goal}
                    </div>
                  </div>
                </div>
              )}

              <div className="cards">
                <div className="card">
                  <div className="label">Iterations</div>
                  <div className="value">{summary?.total ?? selectedRun.rowCount}</div>
                </div>
                <div className="card">
                  <div className="label">Keeps / Success</div>
                  <div className="value">{summary?.outcomes?.success ?? 0}</div>
                </div>
                <div className="card">
                  <div className="label">Discards / Fail</div>
                  <div className="value">{summary?.outcomes?.failure ?? 0}</div>
                </div>
                <div className="card">
                  <div className="label">Best metric</div>
                  <div className="value">
                    {summary?.bestPrimaryValue != null ? summary.bestPrimaryValue : "—"}
                  </div>
                </div>
                {summary?.stuckWarning && (
                  <div className="card warning">
                    <div className="label">Stuck warning</div>
                    <div className="value" style={{ fontSize: "0.9rem" }}>
                      {summary.consecutiveDiscards}+ consecutive discards
                    </div>
                  </div>
                )}
              </div>

              <div className="chart-panel">
                <h2>Progress — {selectedRun.command}</h2>
                <MetricChart command={selectedRun.command} iterations={iterations} />
              </div>

              <div className="chart-panel">
                <h2>Iteration log</h2>
                <IterationTable iterations={iterations} />
              </div>

              <div className="chart-panel">
                <h2>Agent trace</h2>
                <AgentTrace
                  events={traceEvents}
                  artifacts={artifacts}
                  command={selectedRun.command}
                />
              </div>
            </>
          )}
        </div>

        <aside className="sidebar">
          <h2 style={{ margin: "0 0 12px", fontSize: "0.85rem", color: "var(--muted)" }}>
            Git experiments
          </h2>
          <GitTimeline commits={commits} />
        </aside>
      </div>
    </div>
  );
}
