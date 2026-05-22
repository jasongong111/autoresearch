export interface Run {
  runId: string;
  command: string;
  path: string;
  lastModified: number;
  rowCount: number;
  metricDirection?: string;
  headers: string[];
}

export interface Iteration {
  runId: string;
  command: string;
  index: number;
  status: string;
  primaryValue: number | null;
  primaryLabel: string;
  outcome: string;
  description: string;
  location: string;
  commit: string;
  raw: Record<string, string>;
  loggedAt?: string;
}

export interface Summary {
  total: number;
  outcomes: Record<string, number>;
  bestPrimaryValue: number | null;
  consecutiveDiscards: number;
  stuckWarning: boolean;
  statusCounts: Record<string, number>;
  metricDirection?: string;
}

export interface GitCommit {
  hash: string;
  shortHash: string;
  message: string;
  date: string;
}

export interface Session {
  goal?: string;
  scope?: string;
  metric?: string;
  verify?: string;
  command?: string;
  startedAt?: string;
}

export interface TraceEvent {
  ts: string;
  phase: string;
  message: string;
  iteration?: number;
  round?: number;
  detail?: string;
  level: string;
}

export interface TraceArtifact {
  name: string;
  title: string;
  content: string;
  lastModified: number;
  kind: "markdown" | "jsonl";
}
