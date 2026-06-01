import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchConversationTurns,
  fetchConversations,
  fetchExperiments,
  fetchGitCommits,
  fetchHealth,
  fetchInstances,
  fetchIterations,
  fetchRun,
  fetchRunAnalytics,
  fetchRunArtifacts,
  fetchRunExperiments,
  fetchRunGemma3Trace,
  fetchRunGemma4Trace,
  fetchRunTrace,
  fetchRuns,
  fetchSkills,
  fetchSummary,
  subscribeEvents,
} from "../api";
import {
  collectOrchestratorConversationIds,
  conversationIdForInstance,
  getActiveOrchestratorRun,
  patchActiveOrchestratorRun,
  setActiveOrchestratorRun,
} from "../lib/activeRun";
import type {
  ConversationInfo,
  ConversationTurn,
  ExperimentRecord,
  GitCommit,
  Iteration,
  Project,
  Run,
  RunInstance,
  Session,
  SkillDoc,
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
  const [experiments, setExperiments] = useState<ExperimentRecord[]>([]);
  const [skills, setSkills] = useState<SkillDoc[]>([]);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [linkedInstanceId, setLinkedInstanceId] = useState<string | null>(null);
  const [linkedConversationId, setLinkedConversationId] = useState<string | null>(null);
  const [pendingConversationId, setPendingConversationId] = useState<string | null>(null);
  const [orchestratorInstances, setOrchestratorInstances] = useState<RunInstance[]>([]);

  const projectRef = useRef(project);
  const followLiveRef = useRef(followLiveConversation);
  const linkedConversationRef = useRef(linkedConversationId);
  const selectedConversationRef = useRef(selectedConversationId);
  const orchestratorIdsRef = useRef<Set<string>>(new Set());

  projectRef.current = project;
  followLiveRef.current = followLiveConversation;
  linkedConversationRef.current = linkedConversationId;
  selectedConversationRef.current = selectedConversationId;

  const loadConversation = useCallback(async (conversationId: string) => {
    const data = await fetchConversationTurns(conversationId);
    if (data) {
      setConversationTurns(data.turns);
      setPendingConversationId(null);
    }
  }, []);

  const applyOrchestratorLink = useCallback(
    (instance: RunInstance | null, workspaceProject: string, follow = true) => {
      if (!instance) {
        setLinkedInstanceId(null);
        setLinkedConversationId(null);
        return null;
      }
      const convId = conversationIdForInstance(instance, workspaceProject);
      setLinkedInstanceId(instance.id);
      setLinkedConversationId(convId);
      setActiveOrchestratorRun({
        instanceId: instance.id,
        conversationId: convId,
        projectPath: instance.project_path,
      });
      if (follow) {
        setFollowLiveConversation(true);
      }
      return convId;
    },
    []
  );

  const resolveOrchestratorLink = useCallback(
    async (workspaceProject: string, instances: RunInstance[], follow = false) => {
      const stored = getActiveOrchestratorRun();
      const instance =
        (stored ? instances.find((i) => i.id === stored.instanceId) : null) ??
        instances.find((i) => i.status === "running") ??
        null;
      return applyOrchestratorLink(instance, workspaceProject, follow);
    },
    [applyOrchestratorLink]
  );

  const loadConversations = useCallback(
    async (options?: {
      preferredId?: string | null;
      followLinked?: boolean;
      orchestratorConversationId?: string | null;
      instances?: RunInstance[];
    }) => {
      const preferredId = options?.preferredId;
      const followLinked = options?.followLinked ?? false;
      const orchestratorId =
        options?.orchestratorConversationId ??
        linkedConversationRef.current ??
        pendingConversationId;

      const instances = options?.instances ?? (await fetchInstances());
      setOrchestratorInstances(instances);

      const allowedIds = collectOrchestratorConversationIds(instances, projectRef.current);
      orchestratorIdsRef.current = allowedIds;

      const { conversations: allConvs } = await fetchConversations();
      const orchestratorConvs = allConvs.filter((c) => allowedIds.has(c.id));
      setConversations(orchestratorConvs);

      const isAllowed = (id: string | null | undefined) =>
        !!id && (allowedIds.has(id) || id === orchestratorId);

      const pickId = (): string | null => {
        if (followLinked || followLiveRef.current) {
          if (orchestratorId && (orchestratorConvs.some((c) => c.id === orchestratorId) || allowedIds.has(orchestratorId))) {
            return orchestratorId;
          }
          return null;
        }
        if (preferredId && orchestratorConvs.some((c) => c.id === preferredId)) {
          return preferredId;
        }
        if (orchestratorId && orchestratorConvs.some((c) => c.id === orchestratorId)) {
          return orchestratorId;
        }
        if (preferredId && allowedIds.has(preferredId)) {
          return preferredId;
        }
        return orchestratorConvs[0]?.id ?? null;
      };

      const id = pickId();
      setSelectedConversationId(id);

      if (id && orchestratorConvs.some((c) => c.id === id)) {
        setPendingConversationId(null);
        await loadConversation(id);
      } else if (id && isAllowed(id)) {
        setPendingConversationId(id);
        setConversationTurns([]);
      } else {
        setPendingConversationId(null);
        setConversationTurns([]);
      }
    },
    [loadConversation, pendingConversationId]
  );

  const loadRunData = useCallback(async (runId: string) => {
    const [iters, sum, runDetail, agentTrace, gemma3Trace, gemma4Trace, analyticsData, arts, exps] =
      await Promise.all([
        fetchIterations(runId),
        fetchSummary(runId),
        fetchRun(runId),
        fetchRunTrace(runId),
        fetchRunGemma3Trace(runId),
        fetchRunGemma4Trace(runId),
        fetchRunAnalytics(runId),
        fetchRunArtifacts(runId),
        fetchRunExperiments(runId),
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
    setExperiments(exps);
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [health, runsData, gitData, skillsData, instances] = await Promise.all([
        fetchHealth(),
        fetchRuns(),
        fetchGitCommits(selectedProjectId),
        fetchSkills(),
        fetchInstances(),
      ]);
      setProject(health.project);
      const orchestratorConvId = await resolveOrchestratorLink(health.project, instances);
      setProjects(runsData.projects ?? []);
      setRuns(runsData.runs);
      setCommits(gitData);
      setSkills(skillsData);
      await loadConversations({
        preferredId: selectedConversationRef.current,
        orchestratorConversationId: orchestratorConvId,
        instances,
      });
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
        setExperiments([]);
      }
    } finally {
      setLoading(false);
    }
  }, [selectedRunId, selectedProjectId, loadRunData, loadConversations, resolveOrchestratorLink]);

  useEffect(() => {
    refresh();
  }, []);

  useEffect(() => {
    const unsub = subscribeEvents(async (event) => {
      if (event.type === "connected") {
        setConnected(true);
        return;
      }
      if (event.type === "disconnected") {
        setConnected(false);
        return;
      }
      setConnected(true);

      if (event.type === "run_started" && event.instanceId) {
        setActiveOrchestratorRun({
          instanceId: event.instanceId,
          conversationId: event.conversationId ?? null,
          projectPath: event.projectPath,
        });
        setLinkedInstanceId(event.instanceId);
        if (event.conversationId) {
          setLinkedConversationId(event.conversationId);
        }
        setFollowLiveConversation(true);
        setConversationUpdating(true);
        try {
          await loadConversations({
            orchestratorConversationId: event.conversationId ?? linkedConversationRef.current,
            followLinked: true,
          });
        } finally {
          setConversationUpdating(false);
        }
      }

      if (event.type === "instance_updated" && event.instanceId) {
        const active = getActiveOrchestratorRun();
        if (!active || active.instanceId === event.instanceId) {
          if (event.conversationId) {
            setLinkedInstanceId(event.instanceId);
            setLinkedConversationId(event.conversationId);
            patchActiveOrchestratorRun({
              instanceId: event.instanceId,
              conversationId: event.conversationId,
            });
            if (followLiveRef.current) {
              setConversationUpdating(true);
              try {
                await loadConversations({
                  orchestratorConversationId: event.conversationId,
                  followLinked: true,
                });
              } finally {
                setConversationUpdating(false);
              }
            }
          }
        }
      }

      if (event.type === "run_output" && event.instanceId) {
        setOrchestratorInstances((prev) =>
          prev.map((inst) => {
            if (inst.id !== event.instanceId) return inst;
            const tail =
              event.stream === "stdout"
                ? [...inst.stdout_tail, event.line]
                : [...inst.stderr_tail, event.line];
            const trimmed = tail.slice(-250);
            return {
              ...inst,
              [event.stream === "stdout" ? "stdout_tail" : "stderr_tail"]: trimmed,
            };
          })
        );
      }

      if (event.type === "run_updated" && event.instanceId) {
        setOrchestratorInstances((prev) =>
          prev.map((inst) =>
            inst.id === event.instanceId
              ? {
                  ...inst,
                  status: event.status ?? inst.status,
                  exit_code: event.exitCode ?? inst.exit_code,
                }
              : inst
          )
        );
      }

      if (event.type === "run_stopped" && event.instanceId) {
        setOrchestratorInstances((prev) =>
          prev.map((inst) =>
            inst.id === event.instanceId ? { ...inst, status: "stopped" as const } : inst
          )
        );
      }

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
        fetchGitCommits(selectedProjectId).then(setCommits);
      }
      if (event.type === "trace_updated") {
        if (selectedRunId) {
          loadRunData(selectedRunId);
        }
        if (selectedRunId && (!event.runId || event.runId === selectedRunId)) {
          fetchRunArtifacts(selectedRunId).then(setArtifacts);
        }
      }
      if (event.type === "experiment_updated") {
        if (selectedRunId) {
          fetchRunExperiments(selectedRunId).then(setExperiments);
        }
      }
      if (event.type === "conversation_updated") {
        const linked = linkedConversationRef.current;
        const allowed = orchestratorIdsRef.current;
        if (!linked && allowed.size === 0) return;
        if (event.conversationId && linked && event.conversationId !== linked) return;
        if (event.conversationId && allowed.size > 0 && !allowed.has(event.conversationId)) return;

        setConversationUpdating(true);
        const targetId = followLiveRef.current ? linked : selectedConversationRef.current;
        void loadConversations({
          preferredId: targetId,
          followLinked: followLiveRef.current,
          orchestratorConversationId: linked,
        }).finally(() => setConversationUpdating(false));
      }
    });
    setConnected(true);
    return unsub;
  }, [selectedRunId, loadRunData, loadConversations]);

  const handleConversationChange = async (conversationId: string) => {
    setFollowLiveConversation(false);
    setSelectedConversationId(conversationId);
    setPendingConversationId(null);

    const instance = orchestratorInstances.find(
      (i) => conversationIdForInstance(i, projectRef.current) === conversationId
    );
    if (instance) {
      setLinkedInstanceId(instance.id);
      setLinkedConversationId(conversationId);
      setActiveOrchestratorRun({
        instanceId: instance.id,
        conversationId,
        projectPath: instance.project_path,
      });
    }

    await loadConversation(conversationId);
  };

  const handleFollowLiveChange = (value: boolean) => {
    setFollowLiveConversation(value);
    if (value && linkedConversationId) {
      void loadConversations({
        orchestratorConversationId: linkedConversationId,
        followLinked: true,
      });
    }
  };

  const handleProjectChange = async (projectId: string) => {
    setSelectedProjectId(projectId);
    const projectRuns =
      projectId === "all" ? runs : runs.filter((r) => r.projectId === projectId);
    const runId = projectRuns[0]?.runId ?? null;
    setSelectedRunId(runId);
    setCommits(await fetchGitCommits(projectId));
    if (runId) {
      await loadRunData(runId);
    } else {
      setIterations([]);
      setSummary(null);
      setSession(null);
      setTraceStreams([]);
      setAnalytics(null);
      setArtifacts([]);
      setExperiments([]);
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
    setFollowLiveConversation: handleFollowLiveChange,
    handleConversationChange,
    handleProjectChange,
    handleRunChange,
    refresh,
  };
}
