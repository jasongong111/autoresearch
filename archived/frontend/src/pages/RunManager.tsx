import { useState } from "react";
import { Link } from "react-router-dom";
import { Play, Square, Trash2, Terminal, RefreshCw } from "lucide-react";
import { useRuns } from "../hooks/useRuns";
import type { RunConfig, RunInstance } from "../types";

function statusColor(status: string): string {
  switch (status) {
    case "running":
      return "var(--success-fg)";
    case "completed":
      return "var(--info-fg)";
    case "failed":
      return "var(--error-fg)";
    case "stopped":
      return "var(--warning-fg)";
    default:
      return "var(--muted-foreground)";
  }
}

function formatDuration(started?: string, completed?: string): string {
  if (!started) return "—";
  const start = new Date(started).getTime();
  const end = completed ? new Date(completed).getTime() : Date.now();
  const seconds = Math.round((end - start) / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;
  if (minutes < 60) return `${minutes}m ${secs}s`;
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return `${hours}h ${mins}m`;
}

export default function RunManager() {
  const { configs, instances, loading, refresh, runConfig, stopInstance, removeConfig } = useRuns();
  const [selectedInstance, setSelectedInstance] = useState<string | null>(null);

  const instance = instances.find((i) => i.id === selectedInstance);
  const config = configs.find((c) => c.id === instance?.config_id);

  return (
    <div className="dashboard-page">
      <header className="page-header">
        <div className="page-header-row bottom">
          <h1 className="page-title">Run Manager</h1>
          <div className="page-header-spacer" />
          <button type="button" className="btn btn-secondary" onClick={() => refresh()}>
            <RefreshCw size={14} />
            Refresh
          </button>
          <Link to="/runs/new" className="btn btn-primary">
            <Terminal size={14} />
            New Run
          </Link>
        </div>
      </header>

      <div className="page-body">
      {loading && instances.length === 0 ? (
        <div className="loading-grid">
          <div className="skeleton" />
          <div className="skeleton" />
        </div>
      ) : (
        <div className="runs-grid">
          <div className="panel">
            <div className="panel-header">
              <h2 className="panel-title">Instances</h2>
              <span className="badge outline">{instances.length}</span>
            </div>
            <div className="panel-body" style={{ padding: 0 }}>
              {instances.length === 0 ? (
                <p className="empty">No runs yet. Create a configuration and start one.</p>
              ) : (
                <table className="iteration-table">
                  <thead>
                    <tr>
                      <th>Status</th>
                      <th>Config</th>
                      <th>Started</th>
                      <th>Duration</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {instances.map((inst) => {
                      const cfg = configs.find((c) => c.id === inst.config_id);
                      return (
                        <tr
                          key={inst.id}
                          className={selectedInstance === inst.id ? "selected" : ""}
                          onClick={() => setSelectedInstance(inst.id)}
                          style={{ cursor: "pointer" }}
                        >
                          <td>
                            <span
                              className="badge"
                              style={{
                                background: statusColor(inst.status) + "20",
                                color: statusColor(inst.status),
                              }}
                            >
                              {inst.status}
                            </span>
                          </td>
                          <td>{cfg?.name ?? inst.config_id}</td>
                          <td>{inst.started_at ? new Date(inst.started_at).toLocaleString() : "—"}</td>
                          <td>{formatDuration(inst.started_at, inst.completed_at)}</td>
                          <td>
                            <div style={{ display: "flex", gap: 4 }}>
                              {inst.status === "running" && (
                                <button
                                  type="button"
                                  className="btn btn-ghost btn-icon"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    stopInstance(inst.id);
                                  }}
                                  title="Stop"
                                >
                                  <Square size={14} />
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </div>
          </div>

          <div className="panel">
            <div className="panel-header">
              <h2 className="panel-title">Configurations</h2>
              <span className="badge outline">{configs.length}</span>
            </div>
            <div className="panel-body" style={{ padding: 0 }}>
              {configs.length === 0 ? (
                <p className="empty">No saved configurations.</p>
              ) : (
                <table className="iteration-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Command</th>
                      <th>Runner</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {configs.map((cfg) => (
                      <tr key={cfg.id}>
                        <td>{cfg.name}</td>
                        <td>{cfg.command}</td>
                        <td>{cfg.runner}</td>
                        <td>
                          <div style={{ display: "flex", gap: 4 }}>
                            <button
                              type="button"
                              className="btn btn-ghost btn-icon"
                              onClick={() => runConfig(cfg.id)}
                              title="Start"
                            >
                              <Play size={14} />
                            </button>
                            <button
                              type="button"
                              className="btn btn-ghost btn-icon"
                              onClick={() => removeConfig(cfg.id)}
                              title="Delete"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      )}

      {instance && (
        <div className="panel panel-spaced">
          <div className="panel-header">
            <h2 className="panel-title">Logs — {config?.name ?? instance.config_id}</h2>
            <span className="badge outline">{instance.stdout_tail.length + instance.stderr_tail.length} lines</span>
          </div>
          <div
            className="panel-body"
            style={{
              background: "var(--background)",
              fontFamily: "var(--font-mono)",
              fontSize: "0.75rem",
              maxHeight: 400,
              overflow: "auto",
            }}
          >
            {instance.stdout_tail.length === 0 && instance.stderr_tail.length === 0 ? (
              <p style={{ color: "var(--muted-foreground)" }}>No output yet.</p>
            ) : (
              <>
                {instance.stdout_tail.map((line, i) => (
                  <div key={`out-${i}`} style={{ whiteSpace: "pre-wrap" }}>
                    {line}
                  </div>
                ))}
                {instance.stderr_tail.map((line, i) => (
                  <div key={`err-${i}`} style={{ color: "var(--error-fg)", whiteSpace: "pre-wrap" }}>
                    {line}
                  </div>
                ))}
              </>
            )}
          </div>
        </div>
      )}
      </div>
    </div>
  );
}
