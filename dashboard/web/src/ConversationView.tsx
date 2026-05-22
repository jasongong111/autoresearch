import { useEffect, useMemo, useRef, useState } from "react";
import type { ContentBlock, ConversationInfo, ConversationTurn } from "./types";

interface Props {
  conversations: ConversationInfo[];
  turns: ConversationTurn[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  transcriptDirs: string[];
  followLive: boolean;
  onFollowLiveChange: (value: boolean) => void;
  liveUpdating: boolean;
}

type BlockFilter = "all" | "hide_thinking" | "tools_only";

function formatJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function BlockView({ block }: { block: ContentBlock }) {
  switch (block.type) {
    case "text":
      return <div className="conv-text">{block.text}</div>;
    case "thinking":
      return (
        <div className="conv-thinking">
          <span className="conv-block-label">Thinking</span>
          {block.redacted && !block.text ? (
            <em className="conv-muted">Redacted by IDE export</em>
          ) : (
            <pre>{block.text || "(empty)"}</pre>
          )}
        </div>
      );
    case "tool_use":
      return (
        <details className="conv-tool" open>
          <summary>
            <span className="conv-block-label tool">Tool</span> {block.name}
            {block.description ? ` — ${block.description}` : ""}
          </summary>
          <pre>{formatJson(block.input)}</pre>
        </details>
      );
    case "mcp":
      return (
        <details className="conv-tool mcp" open>
          <summary>
            <span className="conv-block-label mcp">MCP</span> {block.server}/{block.toolName}
          </summary>
          <pre>{formatJson(block.arguments)}</pre>
        </details>
      );
    case "tool_result":
      return (
        <details className="conv-tool result">
          <summary>
            <span className="conv-block-label result">Result</span> {block.toolName}
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

export default function ConversationView({
  conversations,
  turns,
  selectedId,
  onSelect,
  transcriptDirs,
  followLive,
  onFollowLiveChange,
  liveUpdating,
}: Props) {
  const [blockFilter, setBlockFilter] = useState<BlockFilter>("all");
  const threadRef = useRef<HTMLDivElement>(null);
  const prevTurnCountRef = useRef(0);

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

  if (conversations.length === 0) {
    return (
      <p className="empty">
        No agent conversations found. The dashboard auto-detects Cursor transcripts at{" "}
        <code>~/.cursor/projects/…/agent-transcripts/</code>, or pass{" "}
        <code>--transcripts-dir</code>. You can also mirror a session to{" "}
        <code>.autoresearch/conversation.jsonl</code>.
      </p>
    );
  }

  return (
    <div className="conv-panel">
      <div className="conv-toolbar">
        <select
          className="select conv-session-select"
          value={selectedId ?? ""}
          onChange={(e) => onSelect(e.target.value)}
        >
          {conversations.map((c) => (
            <option key={c.id} value={c.id}>
              {c.kind === "subagent" ? "↳ " : ""}
              {c.title} ({c.turnCount} turns)
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

      {transcriptDirs.length > 0 && (
        <div className="conv-sources">
          Sources: {transcriptDirs.map((d) => d.split("/").slice(-2).join("/")).join(", ")}
        </div>
      )}

      <div className="conv-thread" ref={threadRef}>
        {turns.map((turn) => {
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
        })}
      </div>
    </div>
  );
}
