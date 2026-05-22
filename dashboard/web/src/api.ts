import type { GitCommit, Iteration, Run, Session, Summary, TraceArtifact, TraceEvent } from "./types";

const API = "/api";

export async function fetchHealth(): Promise<{ project: string; activeRunId: string | null }> {
  const r = await fetch(`${API}/health`);
  return r.json();
}

export async function fetchRuns(): Promise<{ runs: Run[]; activeRunId: string | null }> {
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

export async function fetchGitCommits(): Promise<GitCommit[]> {
  const r = await fetch(`${API}/git/commits`);
  const data = await r.json();
  return data.commits;
}

export async function fetchTrace(): Promise<TraceEvent[]> {
  const r = await fetch(`${API}/trace`);
  if (!r.ok) return [];
  const data = await r.json();
  return data.events ?? [];
}

export async function fetchRunArtifacts(runId: string): Promise<TraceArtifact[]> {
  const r = await fetch(`${API}/runs/${encodeURI(runId)}/artifacts`);
  if (!r.ok) return [];
  const data = await r.json();
  return data.artifacts ?? [];
}

export function subscribeEvents(
  onEvent: (event: { type: string; runId?: string; iterationCount?: number }) => void
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
