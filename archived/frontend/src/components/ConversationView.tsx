import { useEffect, useMemo, useRef, useState } from "react";
import { conversationIdForInstance } from "../lib/activeRun";
import type { ContentBlock, ConversationInfo, ConversationTurn, RunInstance } from "../types";

interface Props {
  conversations: ConversationInfo[];
  turns: ConversationTurn[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  followLive: boolean;
  onFollowLiveChange: (value: boolean) => void;
  liveUpdating: boolean;
  linkedInstanceId?: string | null;
  linkedConversationId?: string | null;
  pendingConversationId?: string | null;
  orchestratorInstances?: RunInstance[];
  workspaceProject?: string;
}

type BlockFilter = "all" | "hide_thinking" | "tools_only";

function formatJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function asText(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function BlockView({ block }: { block: ContentBlock }) {
  switch (block.type) {
    case "text":
      return <div className="conv-text">{asText(block.text)}</div>;
    case "thinking":
      return (
        <div className="conv-thinking">
          <span className="conv-block-label">Thinking</span>
          {block.redacted && !asText(block.text) ? (
            <em className="conv-muted">Redacted by IDE export</em>
          ) : (
            <pre>{asText(block.text, "(empty)")}</pre>
          )}
        </div>
      );
    case "tool_use":
      return (
        <details className="conv-tool" open>
          <summary>
            <span className="conv-block-label tool">Tool</span> {asText(block.name)}
            {asText(block.description) ? ` — ${asText(block.description)}` : ""}
          </summary>
          <pre>{formatJson(block.input)}</pre>
        </details>
      );
    case "mcp":
      return (
        <details className="conv-tool mcp" open>
          <summary>
            <span className="conv-block-label mcp">MCP</span> {asText(block.server)}/{asText(block.toolName)}
          </summary>
          <pre>{formatJson(block.arguments)}</pre>
        </details>
      );
    case "tool_result":
      return (
        <details className="conv-tool result">
          <summary>
            <span className="conv-block-label result">Result</span> {asText(block.toolName)}
            {block.isError ? " (error)" : ""}
          </summary>
          <pre>{typeof block.content === "string" ? block.content : formatJson(block.content)}</pre>
        </details>
      );
    default:
      return (
        <details className="conv-tool">
          <summary>{block.type}</summary>
          <pre>{formatJson(block)}</pre>
        </details>
      );
  }
}

function filterBlocks(blocks: ContentBlock[], filter: BlockFilter): ContentBlock[] {
  if (filter === "all") return blocks;
  if (filter === "hide_thinking") return blocks.filter((b) => b.type !== "thinking");
  return blocks.filter((b) => b.type === "tool_use" || b.type === "mcp" || b.type === "tool_result");
}

function instanceLabel(instance: RunInstance, conv: ConversationInfo | undefined): string {
  const started = instance.started_at
    ? new Date(instance.started_at).toLocaleString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : instance.id;
  if (conv) {
    return `${started} · ${instance.status} · ${conv.title}`;
  }
  return `${started} · ${instance.status} · awaiting transcript`;
}

export default function ConversationView({
  conversations,
  turns,
  selectedId,
  onSelect,
  followLive,
  onFollowLiveChange,
  liveUpdating,
  linkedInstanceId,
  linkedConversationId,
  pendingConversationId,
  orchestratorInstances = [],
  workspaceProject = "",
}: Props) {
  const [blockFilter, setBlockFilter] = useState<BlockFilter>("all");
  const threadRef = useRef<HTMLDivElement>(null);
  const logsRef = useRef<HTMLDivElement>(null);
  const prevTurnCountRef = useRef(0);
  const prevLogCountRef = useRef(0);

  const runOptions = useMemo(() => {
    return orchestratorInstances
      .map((instance) => {
        const conversationId = conversationIdForInstance(instance, workspaceProject);
        if (!conversationId) return null;
        const conv = conversations.find((c) => c.id === conversationId);
        return {
          instanceId: instance.id,
          conversationId,
          label: instanceLabel(instance, conv),
          hasTranscript: !!conv,
        };
      })
      .filter((opt): opt is NonNullable<typeof opt> => opt != null);
  }, [orchestratorInstances, conversations, workspaceProject]);

  const selectedInstance = useMemo(() => {
    return orchestratorInstances.find((i) => {
      const cid = conversationIdForInstance(i, workspaceProject);
      return cid === selectedId;
    });
  }, [orchestratorInstances, selectedId, workspaceProject]);

  useEffect(() => {
    if (turns.length <= prevTurnCountRef.current) {
      prevTurnCountRef.current = turns.length;
      return;
    }
    prevTurnCountRef.current = turns.length;
    const el = threadRef.current;
    if (!el) return;
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 120;
    if (followLive || nearBottom) {
      el.scrollTop = el.scrollHeight;
    }
  }, [turns, followLive]);

  useEffect(() => {
    const logCount = selectedInstance
      ? selectedInstance.stdout_tail.length + selectedInstance.stderr_tail.length
      : 0;
    if (logCount <= prevLogCountRef.current) {
      prevLogCountRef.current = logCount;
      return;
    }
    prevLogCountRef.current = logCount;
    const el = logsRef.current;
    if (!el) return;
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 60;
    if (nearBottom) {
      el.scrollTop = el.scrollHeight;
    }
  }, [selectedInstance]);

  const stats = useMemo(() => {
    let tools = 0;
    let mcp = 0;
    let thinking = 0;
    turns.forEach((t) =>
      t.blocks.forEach((b) => {
        if (b.type === "tool_use") tools += 1;
        if (b.type === "mcp") mcp += 1;
        if (b.type === "thinking") thinking += 1;
      })
    );
    return { tools, mcp, thinking, turns: turns.length };
  }, [turns]);

  if (orchestratorInstances.length === 0 && !pendingConversationId) {
    return (
      <p className="empty">
        No orchestrator runs yet. Start one from the <strong>Runs</strong> page; this tab shows
        conversation for those runs only, not other agent sessions on your machine.
      </p>
    );
  }

  const waitingForTranscript =
    pendingConversationId != null &&
    !conversations.some((c) => c.id === pendingConversationId);

  return (
    <div className="conv-panel">
      {linkedInstanceId && (
        <div className="conv-linked-run">
          Following orchestrator run <code className="mono">{linkedInstanceId}</code>
          {linkedConversationId ? (
            <>
              {" "}
              · conversation <code className="mono">{linkedConversationId.slice(0, 12)}…</code>
            </>
          ) : null}
        </div>
      )}
      <div className="conv-toolbar">
        <select
          className="select conv-session-select"
          value={selectedId ?? pendingConversationId ?? ""}
          onChange={(e) => onSelect(e.target.value)}
        >
          {runOptions.length === 0 && waitingForTranscript && pendingConversationId && (
            <option value={pendingConversationId}>
              Pending transcript ({pendingConversationId.slice(0, 12)}…)
            </option>
          )}
          {runOptions.map((opt) => (
            <option key={opt.instanceId} value={opt.conversationId}>
              {opt.label}
            </option>
          ))}
        </select>
        <select
          className="select"
          value={blockFilter}
          onChange={(e) => setBlockFilter(e.target.value as BlockFilter)}
        >
          <option value="all">All blocks</option>
          <option value="hide_thinking">Hide thinking</option>
          <option value="tools_only">Tools & MCP only</option>
        </select>
        <label className="conv-live-toggle">
          <input
            type="checkbox"
            checked={followLive}
            onChange={(e) => onFollowLiveChange(e.target.checked)}
          />
          Follow live
          {liveUpdating && <span className="conv-live-dot" aria-hidden />}
        </label>
        <span className="conv-stats">
          {stats.turns} turns · {stats.tools} tools · {stats.mcp} MCP · {stats.thinking} thinking
        </span>
      </div>

      {waitingForTranscript && (
        <p className="conv-pending">
          Waiting for agent transcript for <code className="mono">{pendingConversationId}</code>.
          {liveUpdating ? " Checking for updates…" : " It will appear when the agent writes messages."}
        </p>
      )}

      <div className="conv-thread" ref={threadRef}>
        {turns.length === 0 && waitingForTranscript ? (
          <p className="empty">No turns yet for this run.</p>
        ) : turns.length === 0 ? (
          <p className="empty">Select an orchestrator run to view its conversation.</p>
        ) : (
          turns.map((turn) => {
            const blocks = filterBlocks(turn.blocks, blockFilter);
            if (blocks.length === 0) return null;
            return (
              <article key={turn.index} className={`conv-turn ${turn.role}`}>
                <header className="conv-turn-header">
                  <span className="conv-role">{turn.role}</span>
                  <span className="conv-turn-index">#{turn.index + 1}</span>
                </header>
                <div className="conv-blocks">
                  {blocks.map((block, i) => (
                    <BlockView key={`${turn.index}-${i}`} block={block} />
                  ))}
                </div>
              </article>
            );
          })
        )}
      </div>

      {selectedInstance && (
        <div className="conv-logs">
          <div className="conv-logs-header">
            <span className="conv-block-label">Raw logs</span>
            <span className="badge outline">
              {selectedInstance.stdout_tail.length + selectedInstance.stderr_tail.length} lines
            </span>
            <span
              className="badge"
              style={{
                background:
                  selectedInstance.status === "running"
                    ? "var(--success-bg)"
                    : selectedInstance.status === "failed"
                      ? "var(--error-bg)"
                      : "var(--muted-bg)",
                color:
                  selectedInstance.status === "running"
                    ? "var(--success-fg)"
                    : selectedInstance.status === "failed"
                      ? "var(--error-fg)"
                      : "var(--muted-foreground)",
              }}
            >
              {selectedInstance.status === "running" && (
                <span className="conv-live-dot" style={{ display: "inline-block", marginRight: 4 }} aria-hidden />
              )}
              {selectedInstance.status}
            </span>
            {selectedInstance.exit_code != null && (
              <span className="badge outline">exit {selectedInstance.exit_code}</span>
            )}
          </div>
          <div
            ref={logsRef}
            className="conv-logs-body"
            style={{
              background: "var(--background)",
              fontFamily: "var(--font-mono)",
              fontSize: "0.75rem",
              maxHeight: 300,
              overflow: "auto",
              padding: 12,
              borderRadius: 6,
            }}
          >
            {selectedInstance.stdout_tail.length === 0 && selectedInstance.stderr_tail.length === 0 ? (
              <p style={{ color: "var(--muted-foreground)" }}>No output yet.</p>
            ) : (
              <>
                {selectedInstance.stdout_tail.map((line, i) => (
                  <div key={`out-${i}`} style={{ whiteSpace: "pre-wrap" }}>
                    {line}
                  </div>
                ))}
                {selectedInstance.stderr_tail.map((line, i) => (
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
  );
}
