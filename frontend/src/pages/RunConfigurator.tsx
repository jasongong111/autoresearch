import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Save, Play, CheckCircle, AlertCircle } from "lucide-react";
import { useRuns } from "../hooks/useRuns";

const COMMANDS = [
  "autoresearch",
  "autoresearch:plan",
  "autoresearch:debug",
  "autoresearch:fix",
  "autoresearch:security",
  "autoresearch:ship",
  "autoresearch:scenario",
  "autoresearch:predict",
  "autoresearch:learn",
  "autoresearch:reason",
  "autoresearch:probe",
];

const RUNNERS = ["claude", "codex", "opencode", "cursor"];

export default function RunConfigurator() {
  const navigate = useNavigate();
  const { saveConfig, runConfig, dryRunValidate } = useRuns();
  const [form, setForm] = useState({
    name: "",
    command: "autoresearch",
    goal: "",
    scope: "",
    metric: "",
    verify: "",
    guard: "",
    direction: "higher",
    iterations: "",
    runner: "claude",
    cursor_model: "composer-2.5",
    project_path: ".",
  });
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<{
    valid: boolean;
    error?: string;
    numbers?: string[];
  } | null>(null);
  const [saving, setSaving] = useState(false);

  const update = (key: string, value: string) => {
    setForm((f) => ({ ...f, [key]: value }));
    setValidationResult(null);
  };

  const handleValidate = async () => {
    if (!form.verify) return;
    setValidating(true);
    try {
      const result = await dryRunValidate({
        verify: form.verify,
        project_path: form.project_path,
      });
      setValidationResult(result);
    } finally {
      setValidating(false);
    }
  };

  const handleSave = async (andRun = false) => {
    setSaving(true);
    try {
      const config = await saveConfig({
        name: form.name || "Untitled run",
        command: form.command,
        goal: form.goal,
        scope: form.scope,
        metric: form.metric,
        verify: form.verify,
        guard: form.guard || undefined,
        direction: form.direction,
        iterations: form.iterations ? parseInt(form.iterations, 10) : undefined,
        runner: form.runner,
        project_path: form.project_path,
        flags:
          form.runner === "cursor" && form.cursor_model
            ? { model: form.cursor_model }
            : undefined,
      });
      if (andRun) {
        await runConfig(config.id);
      }
      navigate("/runs");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="dashboard-page">
      <header className="page-header">
        <div className="page-header-row bottom">
          <h1 className="page-title">New run</h1>
        </div>
      </header>
      <div className="page-body page-body-narrow">
        <div className="panel">
      <div className="panel-header">
        <h2 className="panel-title">New run configuration</h2>
      </div>
      <div className="panel-body" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <div>
          <label className="metric-label">Name</label>
          <input
            className="input-default"
            style={{ width: "100%" }}
            value={form.name}
            onChange={(e) => update("name", e.target.value)}
            placeholder="e.g., Increase test coverage"
          />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <div>
            <label className="metric-label">Command</label>
            <select
              className="select"
              style={{ width: "100%" }}
              value={form.command}
              onChange={(e) => update("command", e.target.value)}
            >
              {COMMANDS.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="metric-label">Runner</label>
            <select
              className="select"
              style={{ width: "100%" }}
              value={form.runner}
              onChange={(e) => update("runner", e.target.value)}
            >
              {RUNNERS.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
        </div>

        {form.runner === "cursor" && (
          <div>
            <label className="metric-label">Cursor model</label>
            <input
              className="input-default"
              style={{ width: "100%", fontFamily: "var(--font-mono)" }}
              value={form.cursor_model}
              onChange={(e) => update("cursor_model", e.target.value)}
              placeholder="composer-2.5"
            />
            <p style={{ marginTop: 6, fontSize: "0.8rem", color: "var(--muted-fg)" }}>
              Requires <code>CURSOR_API_KEY</code> in the dashboard server environment.
            </p>
          </div>
        )}

        <div>
          <label className="metric-label">Project path</label>
          <input
            className="input-default"
            style={{ width: "100%", fontFamily: "var(--font-mono)" }}
            value={form.project_path}
            onChange={(e) => update("project_path", e.target.value)}
            placeholder="Path to target project directory"
          />
        </div>

        <div>
          <label className="metric-label">Goal</label>
          <textarea
            className="input-default"
            style={{ width: "100%", minHeight: 60, resize: "vertical" }}
            value={form.goal}
            onChange={(e) => update("goal", e.target.value)}
            placeholder="What do you want to achieve?"
          />
        </div>

        <div>
          <label className="metric-label">Scope</label>
          <input
            className="input-default"
            style={{ width: "100%" }}
            value={form.scope}
            onChange={(e) => update("scope", e.target.value)}
            placeholder="e.g., src/**/*.ts"
          />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <div>
            <label className="metric-label">Metric</label>
            <input
              className="input-default"
              style={{ width: "100%" }}
              value={form.metric}
              onChange={(e) => update("metric", e.target.value)}
              placeholder="e.g., coverage %"
            />
          </div>
          <div>
            <label className="metric-label">Direction</label>
            <select
              className="select"
              style={{ width: "100%" }}
              value={form.direction}
              onChange={(e) => update("direction", e.target.value)}
            >
              <option value="higher">Higher is better</option>
              <option value="lower">Lower is better</option>
            </select>
          </div>
        </div>

        <div>
          <label className="metric-label">Verify command</label>
          <div style={{ display: "flex", gap: 8 }}>
            <input
              className="input-default"
              style={{ width: "100%", fontFamily: "var(--font-mono)" }}
              value={form.verify}
              onChange={(e) => update("verify", e.target.value)}
              placeholder="e.g., npm test -- --coverage | grep 'All files'"
            />
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleValidate}
              disabled={!form.verify || validating}
            >
              {validating ? "Testing…" : "Test"}
            </button>
          </div>
          {validationResult && (
            <div
              style={{
                marginTop: 8,
                fontSize: "0.825rem",
                color: validationResult.valid ? "var(--success-fg)" : "var(--error-fg)",
              }}
            >
              {validationResult.valid ? (
                <>
                  <CheckCircle size={14} style={{ verticalAlign: "middle", marginRight: 4 }} />
                  Valid — detected numbers: {validationResult.numbers?.join(", ")}
                </>
              ) : (
                <>
                  <AlertCircle size={14} style={{ verticalAlign: "middle", marginRight: 4 }} />
                  {validationResult.error}
                </>
              )}
            </div>
          )}
        </div>

        <div>
          <label className="metric-label">Guard command (optional)</label>
          <input
            className="input-default"
            style={{ width: "100%", fontFamily: "var(--font-mono)" }}
            value={form.guard}
            onChange={(e) => update("guard", e.target.value)}
            placeholder="e.g., npm test"
          />
        </div>

        <div>
          <label className="metric-label">Iterations (optional)</label>
          <input
            className="input-default"
            style={{ width: "100%" }}
            type="number"
            value={form.iterations}
            onChange={(e) => update("iterations", e.target.value)}
            placeholder="Unbounded if empty"
          />
        </div>

        <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => handleSave(false)}
            disabled={saving}
          >
            <Save size={14} />
            Save
          </button>
          <button
            type="button"
            className="btn btn-accent"
            onClick={() => handleSave(true)}
            disabled={saving || !form.verify}
          >
            <Play size={14} />
            Save & Start
          </button>
        </div>
        </div>
      </div>
    </div>
    </div>
  );
}
