import { useState } from "react";
import {
  GitBranch,
  BarChart3,
  BookOpen,
  LayoutDashboard,
  MessageSquare,
  RefreshCw,
  ScrollText,
  Table2,
  FlaskConical,
} from "lucide-react";
import { useDashboard } from "../hooks/useDashboard";
import AgentTrace from "../components/AgentTrace";
import Analytics from "../components/Analytics";
import ConversationView from "../components/ConversationView";
import ExperimentsView from "../components/ExperimentsView";
import GitTimeline from "../components/GitTimeline";
import IterationTable from "../components/IterationTable";
import MetricChart from "../components/MetricChart";
import SkillsView from "../components/SkillsView";

type Tab = "overview" | "analytics" | "iterations" | "experiments" | "conversation" | "trace" | "git" | "skills";

const TABS: { id: Tab; label: string; icon: typeof LayoutDashboard }[] = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "analytics", label: "Analytics", icon: BarChart3 },
  { id: "iterations", label: "Iterations", icon: Table2 },
  { id: "experiments", label: "Experiments", icon: FlaskConical },
  { id: "conversation", label: "Conversation", icon: MessageSquare },
  { id: "trace", label: "Traces", icon: ScrollText },
  { id: "git", label: "Git", icon: GitBranch },
  { id: "skills", label: "Skills", icon: BookOpen },
];

function shortPath(path: string): string {
  if (!path) return "—";
  const parts = path.split("/");
  if (parts.length <= 3) return path;
  return `…/${parts.slice(-2).join("/")}`;
}

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const db = useDashboard();

  const {
    project,
    projects,
    selectedProjectId,
    runs,
    selectedRunId,
    iterations,
    summary,
    analytics,
    session,
    commits,
    traceStreams,
    artifacts,
    experiments,
    skills,
    conversations,
    conversationTurns,
    selectedConversationId,
    followLiveConversation,
    conversationUpdating,
    linkedInstanceId,
    linkedConversationId,
    pendingConversationId,
    orchestratorInstances,
    connected,
    loading,
    setFollowLiveConversation,
    handleConversationChange,
    handleProjectChange,
    handleRunChange,
    refresh,
  } = db;

  const selectedRun = runs.find((r) => r.runId === selectedRunId);
  const visibleRuns =
    selectedProjectId === "all"
      ? runs
      : runs.filter((r) => r.projectId === selectedProjectId);
  const groupedRuns = visibleRuns.reduce<Record<string, typeof runs>>((acc, r) => {
    (acc[r.command] ??= []).push(r);
    return acc;
  }, {});

  const renderContent = () => {
    if (loading && !selectedRun) {
      return (
        <div className="loading-grid">
          <div className="skeleton" />
          <div className="skeleton" />
          <div className="skeleton tall" />
        </div>
      );
    }

    if (!selectedRun) {
      return (
        <p className="empty">
          {visibleRuns.length === 0 && projects.some((p) => p.isTask) ? (
            <>
              No runs in <code>{selectedProjectId === "all" ? "the watched workspace" : selectedProjectId}</code> yet. Start <code>/autoresearch</code> in that task directory.
            </>
          ) : (
            <>
              No autoresearch runs detected. Start <code>/autoresearch</code> in the watched project.
            </>
          )}
        </p>
      );
    }

    switch (activeTab) {
      case "overview":
        return (
          <div className="overview-layout">
            {session?.goal && (
              <div className="goal-banner">
                <div className="metric-label">Goal</div>
                <p className="goal-text">{session.goal}</p>
              </div>
            )}
            <dl className="stat-strip" aria-label="Run summary">
              <div className="stat-item">
                <dt className="metric-label">Iterations</dt>
                <dd className="metric-value">{summary?.total ?? selectedRun.rowCount}</dd>
              </div>
              <div className="stat-item">
                <dt className="metric-label">Keeps</dt>
                <dd className="metric-value">{summary?.outcomes?.success ?? 0}</dd>
              </div>
              <div className="stat-item">
                <dt className="metric-label">Discards</dt>
                <dd className="metric-value">{summary?.outcomes?.failure ?? 0}</dd>
              </div>
              <div className="stat-item">
                <dt className="metric-label">Best metric</dt>
                <dd className="metric-value">
                  {summary?.bestPrimaryValue != null ? summary.bestPrimaryValue : "—"}
                </dd>
              </div>
              {summary?.stuckWarning && (
                <div className="stat-item warning">
                  <dt className="metric-label">Stuck</dt>
                  <dd className="metric-value">{summary.consecutiveDiscards}+ discards</dd>
                </div>
              )}
            </dl>
            <section className="panel panel-chart" aria-labelledby="progress-heading">
              <div className="panel-header">
                <h2 className="panel-title" id="progress-heading">
                  Progress — {selectedRun.command}
                </h2>
              </div>
              <div className="panel-body panel-body-flush">
                <MetricChart command={selectedRun.command} iterations={iterations} />
              </div>
            </section>
          </div>
        );
      case "analytics":
        return (
          <div className="panel">
            <div className="panel-header">
              <h2 className="panel-title">Loop analytics</h2>
              <span className="badge outline">{analytics?.traces.total ?? 0} traces</span>
            </div>
            <div className="panel-body">
              <Analytics analytics={analytics} />
            </div>
          </div>
        );
      case "iterations":
        return (
          <div className="panel">
            <div className="panel-header">
              <h2 className="panel-title">Iteration log</h2>
              <span className="badge outline">{iterations.length} rows</span>
            </div>
            <div className="panel-body" style={{ padding: 0 }}>
              <IterationTable iterations={iterations} />
            </div>
          </div>
        );
      case "experiments":
        return (
          <div className="panel">
            <div className="panel-header">
              <h2 className="panel-title">Experiments</h2>
              <span className="badge outline">{experiments.length} records</span>
            </div>
            <div className="panel-body">
              <ExperimentsView experiments={experiments} />
            </div>
          </div>
        );
      case "conversation":
        return (
          <div className="panel">
            <div className="panel-header">
              <h2 className="panel-title">Agent conversation</h2>
              {conversations.length > 0 && (
                <span className="badge outline">{conversations.length} sessions</span>
              )}
            </div>
            <div className="panel-body">
              <ConversationView
                conversations={conversations}
                turns={conversationTurns}
                selectedId={selectedConversationId}
                onSelect={handleConversationChange}
                followLive={followLiveConversation}
                onFollowLiveChange={setFollowLiveConversation}
                liveUpdating={conversationUpdating}
                linkedInstanceId={linkedInstanceId}
                linkedConversationId={linkedConversationId}
                pendingConversationId={pendingConversationId}
                orchestratorInstances={orchestratorInstances}
                workspaceProject={project}
              />
            </div>
          </div>
        );
      case "trace":
        return (
          <div className="panel">
            <div className="panel-header">
              <h2 className="panel-title">Traces</h2>
              {traceStreams.some((stream) => stream.events.length > 0) && (
                <span className="badge outline">
                  {traceStreams.reduce((sum, stream) => sum + stream.events.length, 0)} events
                </span>
              )}
            </div>
            <div className="panel-body">
              <AgentTrace
                events={[]}
                artifacts={artifacts}
                command={selectedRun.command}
                traceName="traces"
                tracePath=".autoresearch/trace.jsonl"
                streams={traceStreams}
              />
            </div>
          </div>
        );
      case "git":
        return (
          <div className="panel">
            <div className="panel-header">
              <h2 className="panel-title">Git experiments</h2>
              <span className="badge outline">{commits.length} commits</span>
            </div>
            <div className="panel-body" style={{ padding: 0 }}>
              <GitTimeline commits={commits} />
            </div>
          </div>
        );
      case "skills":
        return (
          <div className="panel">
            <div className="panel-header">
              <h2 className="panel-title">Skill docs</h2>
              <span className="badge outline">{skills.length} files</span>
            </div>
            <div className="panel-body" style={{ padding: 0 }}>
              <SkillsView skills={skills} />
            </div>
          </div>
        );
    }
  };

  return (
    <div className="dashboard-page">
      <header className="page-header">
        <div className="page-header-row top">
          <div className="breadcrumb">
            <span>Project</span>
            <span className="breadcrumb-sep">/</span>
            <span className="breadcrumb-path" title={project}>
              {shortPath(project)}
            </span>
          </div>
          <div className="page-header-spacer" />
          <span className="status-badge">
            <span className={`status-dot ${connected ? "connected" : "disconnected"}`} />
            {connected ? "Live" : "Reconnecting…"}
          </span>
          <button type="button" className="btn btn-secondary" onClick={() => refresh()}>
            <RefreshCw size={14} />
            Refresh
          </button>
        </div>
        <div className="page-header-row bottom">
          {selectedRun && <span className="badge accent">{selectedRun.command}</span>}
          {selectedRun?.projectId && selectedRun.projectId !== "." && (
            <span className="badge outline">{selectedRun.projectId}</span>
          )}
          <h1 className="page-title">{selectedRun ? selectedRun.runId : "Dashboard"}</h1>
          <div className="page-header-spacer" />
          {projects.length > 1 && (
            <select
              className="select"
              value={selectedProjectId}
              onChange={(e) => handleProjectChange(e.target.value)}
              title="Filter by project"
            >
              <option value="all">All projects ({runs.length} runs)</option>
              {projects.map((p) => (
                <option key={p.projectId} value={p.projectId}>
                  {p.projectId === "." ? p.name : p.projectId} ({p.runCount} run{p.runCount === 1 ? "" : "s"})
                </option>
              ))}
            </select>
          )}
          <select
            className="select"
            value={selectedRunId ?? ""}
            onChange={(e) => handleRunChange(e.target.value)}
            disabled={visibleRuns.length === 0}
          >
            {Object.entries(groupedRuns).map(([cmd, cmdRuns]) => (
              <optgroup key={cmd} label={cmd}>
                {cmdRuns.map((r) => (
                  <option key={r.runId} value={r.runId}>
                    {r.projectId && r.projectId !== "." ? `[${r.projectId}] ` : ""}
                    {r.runId} ({r.rowCount} rows)
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
        </div>
      </header>

      <nav className="tabs-bar" aria-label="Dashboard sections">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            className={`tab ${activeTab === id ? "active" : ""}`}
            onClick={() => setActiveTab(id)}
            aria-current={activeTab === id ? "page" : undefined}
          >
            <Icon size={14} aria-hidden />
            <span>{label}</span>
          </button>
        ))}
      </nav>

      <div className="page-body">{renderContent()}</div>
    </div>
  );
}
