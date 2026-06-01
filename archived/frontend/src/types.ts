export interface Project {
  projectId: string;
  projectPath: string;
  name: string;
  runCount: number;
  isTask: boolean;
  gitRoot?: string | null;
}

export interface Run {
  runId: string;
  command: string;
  path: string;
  projectId: string;
  projectPath: string;
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
  projectId?: string;
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
  request?: unknown;
  response?: unknown;
  error?: unknown;
  raw?: unknown;
  [key: string]: unknown;
}

export interface TraceStream {
  id: string;
  title: string;
  path: string;
  events: TraceEvent[];
}

export interface TraceArtifact {
  name: string;
  title: string;
  content: string;
  lastModified: number;
  kind: "markdown" | "jsonl";
}

export interface AnalyticsSummaryRow {
  name: string;
  source?: string;
  dataType?: string;
  count: number;
  average?: number | null;
  zeros?: number;
  ones?: number;
}

export interface AnalyticsSeriesRow {
  bucket: string;
  [key: string]: string | number | Record<string, number> | null;
}

export interface AnalyticsLatencyRow {
  name: string;
  p50Ms: number | null;
  p75Ms?: number | null;
  p90Ms: number | null;
  p95Ms: number | null;
  p99Ms: number | null;
}

export interface ScoreAnalytics {
  name: string;
  source: string;
  dataType: string;
  histogram: { bucket: string; count: number }[];
  categoricalBreakdown: { category: string; count: number }[];
  movingAverage: AnalyticsSeriesRow[];
  categoricalOverTime: { bucket: string; counts: Record<string, number> }[];
}

export interface TraceAnalytics {
  traces: {
    total: number;
    byName: { name: string; count: number }[];
  };
  modelCosts: {
    totalCostUsd: number;
    byModel: { model: string; tokens: number; costUsd: number }[];
  };
  scores: {
    total: number;
    summary: AnalyticsSummaryRow[];
  };
  timeSeries: {
    traceObservationByLevel: {
      bucket: string;
      traceCount: number;
      observationCount: number;
      observationsByLevel: Record<string, number>;
    }[];
    observationsByLevel: {
      bucket: string;
      observationsByLevel: Record<string, number>;
    }[];
  };
  modelUsage: {
    models: string[];
    costByModel: AnalyticsSeriesRow[];
    costByType: AnalyticsSeriesRow[];
    usageByModel: AnalyticsSeriesRow[];
    usageByType: AnalyticsSeriesRow[];
  };
  userConsumption: {
    costByUser: { user: string; totalCostUsd: number }[];
    traceCountByUser: { user: string; traceCount: number }[];
  };
  scoreTimeSeries: AnalyticsSeriesRow[];
  latencies: {
    trace: AnalyticsLatencyRow[];
    generation: AnalyticsLatencyRow[];
    observation: AnalyticsLatencyRow[];
  };
  modelLatencies: {
    series: (AnalyticsSeriesRow & { model: string })[];
  };
  scoreAnalytics: Record<string, ScoreAnalytics>;
}

export type ContentBlock =
  | { type: "text"; text: string }
  | { type: "thinking"; text: string; redacted?: boolean }
  | { type: "tool_use"; name: string; input: Record<string, unknown>; description?: string; subagentType?: string }
  | { type: "mcp"; server: string; toolName: string; arguments: Record<string, unknown> }
  | { type: "tool_result"; toolName: string; content: unknown; isError?: boolean }
  | { type: string; [key: string]: unknown };

export interface ConversationInfo {
  id: string;
  title: string;
  path: string;
  lastModified: number;
  turnCount: number;
  kind: "cursor" | "subagent" | "local" | "claude";
  parentId?: string | null;
}

export interface ConversationTurn {
  index: number;
  role: string;
  blocks: ContentBlock[];
}

export interface SkillDoc {
  id: string;
  path: string;
  name: string;
  category: string;
  source: string;
  lastModified: number;
  size: number;
}

export interface RunConfig {
  id: string;
  name: string;
  command: string;
  goal: string;
  scope: string;
  metric: string;
  verify: string;
  guard?: string;
  direction?: string;
  iterations?: number;
  flags: Record<string, unknown>;
  runner: string;
  project_path: string;
  created_at: string;
  updated_at: string;
}

export interface RunInstance {
  id: string;
  config_id: string;
  status: "queued" | "running" | "completed" | "failed" | "stopped";
  pid?: number;
  started_at?: string;
  completed_at?: string;
  exit_code?: number;
  stdout_tail: string[];
  stderr_tail: string[];
  project_path?: string;
  conversation_id?: string | null;
  cursor_agent_id?: string | null;
}

export interface ExperimentRecord {
  iteration: number;
  timestamp: string;
  status: string;
  commit: string;
  metric: number | null;
  delta: number | null;
  guard: string;
  guardMetric?: number | null;
  description: string;
  hypothesis?: string;
  filesRead?: string[];
  filesModified?: string[];
  toolsUsed?: { name: string; input: Record<string, unknown> }[];
  verifyOutput?: string;
  guardOutput?: string;
  durationMs?: number;
  [key: string]: unknown;
}
