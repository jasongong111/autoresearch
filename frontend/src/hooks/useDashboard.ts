import { useCallback, useEffect, useState } from "react";
import {
  fetchConversationTurns,
  fetchConversations,
  fetchGitCommits,
  fetchHealth,
  fetchIterations,
  fetchRun,
  fetchRunAnalytics,
  fetchRunArtifacts,
  fetchRunGemma3Trace,
  fetchRunGemma4Trace,
  fetchRunTrace,
  fetchRuns,
  fetchSummary,
  subscribeEvents,
} from "../api";
import type {
  ConversationInfo,
  ConversationTurn,
  GitCommit,
  Iteration,
  Project,
  Run,
  Session,
  Summary,
  TraceAnalytics,
  TraceArtifact,
  TraceStream,
} from "../types";

export function useDashboard() {
  const [project, setProject] = useState("");
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("all");
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [iterations, setIterations] = useState<Iteration[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [analytics, setAnalytics] = useState<TraceAnalytics | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [commits, setCommits] = useState<GitCommit[]>([]);
  const [traceStreams, setTraceStreams] = useState<TraceStream[]>([]);
  const [artifacts, setArtifacts] = useState<TraceArtifact[]>([]);
  const [conversations, setConversations] = useState<ConversationInfo[]>([]);
  const [conversationTurns, setConversationTurns] = useState<ConversationTurn[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [followLiveConversation, setFollowLiveConversation] = useState(true);
  const [conversationUpdating, setConversationUpdating] = useState(false);
  const [transcriptDirs, setTranscriptDirs] = useState<string[]>([]);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadConversation = useCallback(async (conversationId: string) => {
    const data = await fetchConversationTurns(conversationId);
    if (data) {
      setConversationTurns(data.turns);
    }
  }, []);

  const loadConversations = useCallback(
    async (options?: { preferredId?: string | null; followLatest?: boolean }) => {
      const preferredId = options?.preferredId;
      const followLatest = options?.followLatest ?? false;
      const { conversations: convs, transcriptDirs: dirs } = await fetchConversations();
      setConversations(convs);
      setTranscriptDirs(dirs);
      let id =
        preferredId && convs.some((c) => c.id === preferredId)
          ? preferredId
          : convs[0]?.id ?? null;
      if ((followLatest || followLiveConversation) && convs.length > 0) {
        id = convs[0].id;
      }
      setSelectedConversationId(id);
      if (id) {
        await loadConversation(id);
      } else {
        setConversationTurns([]);
      }
    },
    [loadConversation, followLiveConversation]
  );

  const loadRunData = useCallback(async (runId: string) => {
    const [iters, sum, runDetail, agentTrace, gemma3Trace, gemma4Trace, analyticsData, arts] = await Promise.all([
      fetchIterations(runId),
      fetchSummary(runId),
      fetchRun(runId),
      fetchRunTrace(runId),
      fetchRunGemma3Trace(runId),
      fetchRunGemma4Trace(runId),
      fetchRunAnalytics(runId),
      fetchRunArtifacts(runId),
    ]);
    setIterations(iters);
    setSummary(sum);
    setSession(runDetail.session);
    setTraceStreams([
      {
        id: "agent",
        title: "Agent observer",
        path: ".autoresearch/trace.jsonl",
        events: agentTrace,
      },
      {
        id: "gemma3",
        title: "Gemma 3 API",
        path: ".autoresearch/gemma3-trace.jsonl",
        events: gemma3Trace,
      },
      {
        id: "gemma4",
        title: "Gemma 4 API",
        path: ".autoresearch/gemma4-trace.jsonl",
        events: gemma4Trace,
      },
    ]);
    setAnalytics(analyticsData);
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
      setProjects(runsData.projects ?? []);
      setRuns(runsData.runs);
      setCommits(gitData);
      await loadConversations({ preferredId: selectedConversationId });
      const projectRuns =
        selectedProjectId === "all"
          ? runsData.runs
          : runsData.runs.filter((r) => r.projectId === selectedProjectId);
      const active = runsData.activeRunId ?? runsData.runs[0]?.runId ?? null;
      const runId =
        selectedRunId && projectRuns.some((r) => r.runId === selectedRunId)
          ? selectedRunId
          : projectRuns[0]?.runId ?? (selectedProjectId === "all" ? active : null);
      if (runId) {
        setSelectedRunId(runId);
        await loadRunData(runId);
      } else {
        setSelectedRunId(null);
        setIterations([]);
        setSummary(null);
        setSession(null);
        setTraceStreams([]);
        setAnalytics(null);
        setArtifacts([]);
      }
    } finally {
      setLoading(false);
    }
  }, [selectedRunId, selectedProjectId, selectedConversationId, loadRunData, loadConversations]);

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
        fetchRuns().then((d) => {
          setProjects(d.projects ?? []);
          setRuns(d.runs);
        });
      }
      if (event.type === "git_updated") {
        fetchGitCommits().then(setCommits);
      }
      if (event.type === "trace_updated") {
        if (selectedRunId) {
          loadRunData(selectedRunId);
        }
        if (selectedRunId && (!event.runId || event.runId === selectedRunId)) {
          fetchRunArtifacts(selectedRunId).then(setArtifacts);
        }
      }
      if (event.type === "conversation_updated") {
        setConversationUpdating(true);
        void loadConversations({
          preferredId: followLiveConversation ? event.conversationId : selectedConversationId,
          followLatest: followLiveConversation,
        }).finally(() => setConversationUpdating(false));
      }
    });
    setConnected(true);
    return unsub;
  }, [selectedRunId, loadRunData, loadConversations, selectedConversationId, followLiveConversation]);

  const handleConversationChange = async (conversationId: string) => {
    setFollowLiveConversation(false);
    setSelectedConversationId(conversationId);
    await loadConversation(conversationId);
  };

  const handleProjectChange = async (projectId: string) => {
    setSelectedProjectId(projectId);
    const projectRuns =
      projectId === "all" ? runs : runs.filter((r) => r.projectId === projectId);
    const runId = projectRuns[0]?.runId ?? null;
    setSelectedRunId(runId);
    if (runId) {
      await loadRunData(runId);
    } else {
      setIterations([]);
      setSummary(null);
      setSession(null);
      setTraceStreams([]);
      setAnalytics(null);
      setArtifacts([]);
    }
  };

  const handleRunChange = async (runId: string) => {
    setSelectedRunId(runId);
    await loadRunData(runId);
  };

  return {
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
    conversations,
    conversationTurns,
    selectedConversationId,
    followLiveConversation,
    conversationUpdating,
    transcriptDirs,
    connected,
    loading,
    setFollowLiveConversation,
    handleConversationChange,
    handleProjectChange,
    handleRunChange,
    refresh,
  };
}
