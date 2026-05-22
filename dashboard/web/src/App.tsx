import { useCallback, useEffect, useState } from "react";
import {
  Activity,
  GitBranch,
  LayoutDashboard,
  MessageSquare,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  RefreshCw,
  ScrollText,
  Sun,
  Table2,
} from "lucide-react";
import {
  fetchConversationTurns,
  fetchConversations,
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
import ConversationView from "./ConversationView";
import GitTimeline from "./GitTimeline";
import IterationTable from "./IterationTable";
import MetricChart from "./MetricChart";
import type {
  ConversationInfo,
  ConversationTurn,
  GitCommit,
  Iteration,
  Run,
  Session,
  Summary,
  TraceArtifact,
  TraceEvent,
} from "./types";

type Tab = "overview" | "iterations" | "conversation" | "trace" | "git";

const TABS: { id: Tab; label: string; icon: typeof LayoutDashboard }[] = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "iterations", label: "Iterations", icon: Table2 },
  { id: "conversation", label: "Conversation", icon: MessageSquare },
  { id: "trace", label: "Agent trace", icon: ScrollText },
  { id: "git", label: "Git", icon: GitBranch },
];

function useTheme() {
  const [theme, setTheme] = useState<"light" | "dark" | "system">(() => {
    return (localStorage.getItem("dashboard-theme") as "light" | "dark" | "system") ?? "system";
  });
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const root = document.documentElement;
    localStorage.setItem("dashboard-theme", theme);
    if (theme === "light") {
      root.setAttribute("data-theme", "light");
      root.classList.remove("dark");
      setIsDark(false);
    } else if (theme === "dark") {
      root.setAttribute("data-theme", "dark");
      root.classList.add("dark");
      setIsDark(true);
    } else {
      root.removeAttribute("data-theme");
      root.classList.remove("dark");
      const mq = window.matchMedia("(prefers-color-scheme: dark)");
      setIsDark(mq.matches);
      const handler = (e: MediaQueryListEvent) => setIsDark(e.matches);
      mq.addEventListener("change", handler);
      return () => mq.removeEventListener("change", handler);
    }
  }, [theme]);

  const toggle = () => setTheme(isDark ? "light" : "dark");

  return { isDark, toggle };
}

function shortPath(path: string): string {
  if (!path) return "—";
  const parts = path.split("/");
  if (parts.length <= 3) return path;
  return `…/${parts.slice(-2).join("/")}`;
}

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
  const [conversations, setConversations] = useState<ConversationInfo[]>([]);
  const [conversationTurns, setConversationTurns] = useState<ConversationTurn[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [transcriptDirs, setTranscriptDirs] = useState<string[]>([]);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(
    () => localStorage.getItem("dashboard-sidebar-collapsed") === "true"
  );
  const { isDark, toggle: toggleTheme } = useTheme();

  const toggleSidebar = () => {
    setSidebarCollapsed((c) => {
      const next = !c;
      localStorage.setItem("dashboard-sidebar-collapsed", String(next));
      return next;
    });
  };

  const loadConversation = useCallback(async (conversationId: string) => {
    const data = await fetchConversationTurns(conversationId);
    if (data) {
      setConversationTurns(data.turns);
    }
  }, []);

  const loadConversations = useCallback(async (preferredId?: string | null) => {
    const { conversations: convs, transcriptDirs: dirs } = await fetchConversations();
    setConversations(convs);
    setTranscriptDirs(dirs);
    const id =
      preferredId && convs.some((c) => c.id === preferredId)
        ? preferredId
        : convs[0]?.id ?? null;
    setSelectedConversationId(id);
    if (id) {
      await loadConversation(id);
    } else {
      setConversationTurns([]);
    }
  }, [loadConversation]);

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
      await loadConversations(selectedConversationId);
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
  }, [selectedRunId, selectedConversationId, loadRunData, loadConversations]);

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
      if (event.type === "conversation_updated") {
        loadConversations(selectedConversationId);
      }
    });
    setConnected(true);
    return unsub;
  }, [selectedRunId, loadRunData, loadConversations, selectedConversationId]);

  const handleConversationChange = async (conversationId: string) => {
    setSelectedConversationId(conversationId);
    await loadConversation(conversationId);
  };

  const handleRunChange = async (runId: string) => {
    setSelectedRunId(runId);
    await loadRunData(runId);
  };

  const selectedRun = runs.find((r) => r.runId === selectedRunId);
  const groupedRuns = runs.reduce<Record<string, Run[]>>((acc, r) => {
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
          No autoresearch runs detected. Start <code>/autoresearch</code> in the watched project.
        </p>
      );
    }

    switch (activeTab) {
      case "overview":
        return (
          <>
            {session?.goal && (
              <div className="goal-banner">
                <div className="metric-label">Goal</div>
                {session.goal}
              </div>
            )}

            <div className="metrics-row">
              <div className="metric-cell">
                <div className="metric-label">Iterations</div>
                <div className="metric-value">{summary?.total ?? selectedRun.rowCount}</div>
              </div>
              <div className="metric-cell">
                <div className="metric-label">Keeps</div>
                <div className="metric-value">{summary?.outcomes?.success ?? 0}</div>
              </div>
              <div className="metric-cell">
                <div className="metric-label">Discards</div>
                <div className="metric-value">{summary?.outcomes?.failure ?? 0}</div>
              </div>
              <div className="metric-cell">
                <div className="metric-label">Best metric</div>
                <div className="metric-value">
                  {summary?.bestPrimaryValue != null ? summary.bestPrimaryValue : "—"}
                </div>
              </div>
              {summary?.stuckWarning && (
                <div className="metric-cell warning">
                  <div className="metric-label">Stuck</div>
                  <div className="metric-value">{summary.consecutiveDiscards}+ discards</div>
                </div>
              )}
            </div>

            <div className="panel">
              <div className="panel-header">
                <h2 className="panel-title">Progress — {selectedRun.command}</h2>
              </div>
              <div className="panel-body">
                <MetricChart command={selectedRun.command} iterations={iterations} />
              </div>
            </div>
          </>
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
                transcriptDirs={transcriptDirs}
              />
            </div>
          </div>
        );

      case "trace":
        return (
          <div className="panel">
            <div className="panel-header">
              <h2 className="panel-title">Agent trace</h2>
              {traceEvents.length > 0 && (
                <span className="badge outline">{traceEvents.length} events</span>
              )}
            </div>
            <div className="panel-body">
              <AgentTrace
                events={traceEvents}
                artifacts={artifacts}
                command={selectedRun.command}
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
    }
  };

  return (
    <div className="app-shell">
      <aside className={`sidebar ${sidebarCollapsed ? "collapsed" : ""}`}>
        <div className="sidebar-brand">
          <Activity className="sidebar-brand-icon" size={18} />
          <span className="sidebar-brand-text">Autoresearch</span>
        </div>

        <nav className="sidebar-nav">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              className={`nav-item ${activeTab === id ? "active" : ""}`}
              onClick={() => setActiveTab(id)}
              title={label}
            >
              <Icon size={16} />
              <span>{label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <button
            type="button"
            className="nav-item"
            onClick={toggleSidebar}
            title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {sidebarCollapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
            <span>Collapse</span>
          </button>
        </div>
      </aside>

      <div className="main-area">
        <header className="page-header">
          <div className="page-header-row top">
            <button
              type="button"
              className="btn btn-ghost btn-icon"
              onClick={toggleSidebar}
              title="Toggle sidebar"
            >
              <PanelLeftOpen size={16} />
            </button>
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
            <button type="button" className="btn btn-ghost btn-icon" onClick={toggleTheme} title="Toggle theme">
              {isDark ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            <button type="button" className="btn btn-secondary" onClick={() => refresh()}>
              <RefreshCw size={14} />
              Refresh
            </button>
          </div>

          <div className="page-header-row bottom">
            {selectedRun && (
              <span className="badge accent">{selectedRun.command}</span>
            )}
            <h1 className="page-title">
              {selectedRun ? selectedRun.runId : "Dashboard"}
            </h1>
            <div className="page-header-spacer" />
            <select
              className="select"
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
          </div>
        </header>

        <div className="tabs-bar">
          {TABS.map(({ id, label }) => (
            <button
              key={id}
              type="button"
              className={`tab ${activeTab === id ? "active" : ""}`}
              onClick={() => setActiveTab(id)}
            >
              {label}
            </button>
          ))}
        </div>

        <main className="page-content">{renderContent()}</main>
      </div>
    </div>
  );
}
