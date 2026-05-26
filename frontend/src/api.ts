import type {
  ConversationInfo,
  ConversationTurn,
  ExperimentRecord,
  GitCommit,
  Iteration,
  Project,
  Run,
  RunConfig,
  RunInstance,
  Session,
  SkillDoc,
  Summary,
  TraceAnalytics,
  TraceArtifact,
  TraceEvent,
} from "./types";

const API = "/api";

export async function fetchHealth(): Promise<{ project: string; activeRunId: string | null }> {
  const r = await fetch(`${API}/health`);
  return r.json();
}

export async function fetchProjects(): Promise<Project[]> {
  const r = await fetch(`${API}/projects`);
  if (!r.ok) return [];
  const data = await r.json();
  return data.projects ?? [];
}

export async function fetchRuns(): Promise<{
  runs: Run[];
  projects: Project[];
  activeRunId: string | null;
}> {
  const r = await fetch(`${API}/runs`);
  return r.json();
}

export async function fetchRun(
  runId: string
): Promise<Run & { session: Session | null; isActive: boolean }> {
  const r = await fetch(`${API}/runs/${encodeURI(runId)}`);
  if (!r.ok) throw new Error(`Run not found: ${runId}`);
  return r.json();
}

export async function fetchIterations(runId: string): Promise<Iteration[]> {
  const r = await fetch(`${API}/runs/${encodeURI(runId)}/iterations`);
  if (!r.ok) throw new Error(`Iterations not found: ${runId}`);
  const data = await r.json();
  return data.iterations;
}

export async function fetchSummary(runId: string): Promise<Summary> {
  const r = await fetch(`${API}/runs/${encodeURI(runId)}/summary`);
  if (!r.ok) throw new Error(`Summary not found: ${runId}`);
  return r.json();
}

export async function fetchGitCommits(projectId?: string): Promise<GitCommit[]> {
  const query =
    projectId && projectId !== "all"
      ? `?project_id=${encodeURIComponent(projectId)}`
      : "";
  const r = await fetch(`${API}/git/commits${query}`);
  const data = await r.json();
  return data.commits;
}

export async function fetchTrace(): Promise<TraceEvent[]> {
  const r = await fetch(`${API}/trace`);
  if (!r.ok) return [];
  const data = await r.json();
  return data.events ?? [];
}

export async function fetchAnalytics(): Promise<TraceAnalytics | null> {
  const r = await fetch(`${API}/analytics`);
  if (!r.ok) return null;
  return r.json();
}

export async function fetchRunTrace(runId: string): Promise<TraceEvent[]> {
  const r = await fetch(`${API}/runs/${encodeURI(runId)}/trace`);
  if (!r.ok) return [];
  const data = await r.json();
  return data.events ?? [];
}

export async function fetchRunGemma4Trace(runId: string): Promise<TraceEvent[]> {
  const r = await fetch(`${API}/runs/${encodeURI(runId)}/gemma4-trace`);
  if (!r.ok) return [];
  const data = await r.json();
  return data.events ?? [];
}

export async function fetchRunGemma3Trace(runId: string): Promise<TraceEvent[]> {
  const r = await fetch(`${API}/runs/${encodeURI(runId)}/gemma3-trace`);
  if (!r.ok) return [];
  const data = await r.json();
  return data.events ?? [];
}

export async function fetchRunAnalytics(runId: string): Promise<TraceAnalytics | null> {
  const r = await fetch(`${API}/runs/${encodeURI(runId)}/analytics`);
  if (!r.ok) return null;
  return r.json();
}

export async function fetchRunArtifacts(runId: string): Promise<TraceArtifact[]> {
  const r = await fetch(`${API}/runs/${encodeURI(runId)}/artifacts`);
  if (!r.ok) return [];
  const data = await r.json();
  return data.artifacts ?? [];
}

export async function fetchExperiments(): Promise<ExperimentRecord[]> {
  const r = await fetch(`${API}/experiments`);
  if (!r.ok) return [];
  const data = await r.json();
  return data.experiments ?? [];
}

export async function fetchRunExperiments(runId: string): Promise<ExperimentRecord[]> {
  const r = await fetch(`${API}/runs/${encodeURI(runId)}/experiments`);
  if (!r.ok) return [];
  const data = await r.json();
  return data.experiments ?? [];
}

export async function fetchSkills(): Promise<SkillDoc[]> {
  const r = await fetch(`${API}/skills`);
  if (!r.ok) return [];
  const data = await r.json();
  return data.skills ?? [];
}

export async function fetchSkillContent(docId: string): Promise<string | null> {
  const r = await fetch(`${API}/skills/${encodeURI(docId)}`);
  if (!r.ok) return null;
  const data = await r.json();
  return data.content ?? null;
}

export async function fetchConversations(): Promise<{
  conversations: ConversationInfo[];
  transcriptDirs: string[];
}> {
  const r = await fetch(`${API}/conversations`);
  if (!r.ok) return { conversations: [], transcriptDirs: [] };
  const data = await r.json();
  return {
    conversations: data.conversations ?? [],
    transcriptDirs: data.transcriptDirs ?? [],
  };
}

export async function fetchConversationTurns(
  conversationId: string
): Promise<{ conversation: ConversationInfo; turns: ConversationTurn[] } | null> {
  const r = await fetch(`${API}/conversations/${encodeURI(conversationId)}/turns`);
  if (!r.ok) return null;
  return r.json();
}

export async function fetchConfigs(): Promise<RunConfig[]> {
  const r = await fetch(`${API}/orchestrator/configs`);
  if (!r.ok) return [];
  const data = await r.json();
  return data.configs ?? [];
}

export async function fetchConfig(configId: string): Promise<RunConfig | null> {
  const r = await fetch(`${API}/orchestrator/configs/${encodeURIComponent(configId)}`);
  if (!r.ok) return null;
  return r.json();
}

export async function createConfig(config: Partial<RunConfig>): Promise<RunConfig> {
  const r = await fetch(`${API}/orchestrator/configs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  if (!r.ok) throw new Error("Failed to create config");
  return r.json();
}

export async function updateConfig(configId: string, config: Partial<RunConfig>): Promise<RunConfig> {
  const r = await fetch(`${API}/orchestrator/configs/${encodeURIComponent(configId)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  if (!r.ok) throw new Error("Failed to update config");
  return r.json();
}

export async function deleteConfig(configId: string): Promise<void> {
  const r = await fetch(`${API}/orchestrator/configs/${encodeURIComponent(configId)}`, {
    method: "DELETE",
  });
  if (!r.ok) throw new Error("Failed to delete config");
}

export async function startRun(configId: string): Promise<RunInstance> {
  const r = await fetch(`${API}/orchestrator/configs/${encodeURIComponent(configId)}/start`, {
    method: "POST",
  });
  if (!r.ok) throw new Error("Failed to start run");
  return r.json();
}

export async function stopRun(instanceId: string): Promise<void> {
  const r = await fetch(`${API}/orchestrator/instances/${encodeURIComponent(instanceId)}/stop`, {
    method: "POST",
  });
  if (!r.ok) throw new Error("Failed to stop run");
}

export async function fetchInstances(): Promise<RunInstance[]> {
  const r = await fetch(`${API}/orchestrator/instances`);
  if (!r.ok) return [];
  const data = await r.json();
  return data.instances ?? [];
}

export async function fetchInstance(instanceId: string): Promise<RunInstance | null> {
  const r = await fetch(`${API}/orchestrator/instances/${encodeURIComponent(instanceId)}`);
  if (!r.ok) return null;
  return r.json();
}

export async function fetchInstanceLogs(instanceId: string): Promise<{ stdout: string[]; stderr: string[] }> {
  const r = await fetch(`${API}/orchestrator/instances/${encodeURIComponent(instanceId)}/logs`);
  if (!r.ok) return { stdout: [], stderr: [] };
  return r.json();
}

export async function validateConfig(data: Partial<RunConfig>): Promise<{ valid: boolean; error?: string; numbers?: string[]; output?: string; exitCode?: number }> {
  const r = await fetch(`${API}/orchestrator/configs/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!r.ok) return { valid: false, error: "Validation request failed" };
  return r.json();
}

export function subscribeEvents(
  onEvent: (event: {
    type: string;
    runId?: string;
    iterationCount?: number;
    conversationId?: string;
    instanceId?: string;
    configId?: string;
    runner?: string;
    projectPath?: string;
    cursorAgentId?: string;
    cursorRunId?: string;
    status?: string;
    stream?: string;
    line?: string;
  }) => void
): () => void {
  const es = new EventSource(`${API}/events`);
  es.onmessage = (e) => {
    try {
      onEvent(JSON.parse(e.data));
    } catch {
      /* ignore */
    }
  };
  es.onerror = () => {
    onEvent({ type: "disconnected" });
  };
  return () => es.close();
}
