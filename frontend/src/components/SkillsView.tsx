import { useEffect, useMemo, useState } from "react";
import { fetchSkillContent } from "../api";
import type { SkillDoc } from "../types";

interface Props {
  skills: SkillDoc[];
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function categoryIcon(category: string): string {
  if (category === "skill") return "⚡";
  if (category === "reference") return "📖";
  if (category === "command") return "⌘";
  if (category === "script") return "🛠️";
  if (category === "resource") return "📦";
  return "📄";
}

export default function SkillsView({ skills }: Props) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [content, setContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const categories = useMemo(() => {
    const map = new Map<string, SkillDoc[]>();
    for (const s of skills) {
      const list = map.get(s.category) ?? [];
      list.push(s);
      map.set(s.category, list);
    }
    return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [skills]);

  useEffect(() => {
    if (!selectedId) {
      setContent(null);
      return;
    }
    setLoading(true);
    fetchSkillContent(selectedId)
      .then((c) => setContent(c))
      .finally(() => setLoading(false));
  }, [selectedId]);

  if (skills.length === 0) {
    return (
      <p className="empty">
        No skill files found under <code>.claude/skills/</code>,{" "}
        <code>.agents/skills/</code>, or <code>plugins/</code>.
      </p>
    );
  }

  return (
    <div className="skills-panel">
      <div className="skills-sidebar">
        {categories.map(([category, docs]) => (
          <div key={category} className="skills-category">
            <div className="skills-category-header">
              {categoryIcon(category)} {category}
            </div>
            <ul className="skills-list">
              {docs.map((doc) => (
                <li key={doc.id}>
                  <button
                    type="button"
                    className={`skills-item ${selectedId === doc.id ? "active" : ""}`}
                    onClick={() => setSelectedId(doc.id)}
                    title={doc.id}
                  >
                    <span className="skills-name">{doc.name}</span>
                    <span className="skills-meta">{formatSize(doc.size)}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="skills-content">
        {selectedId ? (
          <>
            <div className="skills-content-header">
              <code>{selectedId}</code>
            </div>
            {loading ? (
              <div className="skeleton" style={{ height: "80%" }} />
            ) : content != null ? (
              <pre className="skills-doc">{content}</pre>
            ) : (
              <p className="empty">Failed to load content.</p>
            )}
          </>
        ) : (
          <p className="empty">Select a skill doc from the sidebar.</p>
        )}
      </div>
    </div>
  );
}
