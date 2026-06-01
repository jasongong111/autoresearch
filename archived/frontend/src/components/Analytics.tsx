import { useMemo, useState } from "react";
import type {
  AnalyticsLatencyRow,
  AnalyticsSeriesRow,
  ScoreAnalytics,
  TraceAnalytics,
} from "../types";

interface Props {
  analytics: TraceAnalytics | null;
}

type UsageTab = "costModel" | "costType" | "usageModel" | "usageType";

const USAGE_TABS: { id: UsageTab; label: string }[] = [
  { id: "costModel", label: "Cost by model" },
  { id: "costType", label: "Cost by type" },
  { id: "usageModel", label: "Usage by model" },
  { id: "usageType", label: "Usage by type" },
];

function formatUsd(value: number | null | undefined): string {
  if (value == null) return "—";
  return `$${value.toFixed(value < 1 ? 4 : 2)}`;
}

function formatNum(value: number | string | null | undefined): string {
  if (value == null) return "—";
  if (typeof value === "string") return value;
  return Number.isInteger(value) ? value.toLocaleString() : value.toFixed(2);
}

function formatBucket(bucket: string): string {
  if (!bucket || bucket === "unknown") return "unknown";
  try {
    const date = new Date(bucket);
    if (Number.isNaN(date.getTime())) return bucket;
    return date.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit" });
  } catch {
    return bucket;
  }
}

function BarList<T>({
  rows,
  label,
  value,
  format = formatNum,
}: {
  rows: T[];
  label: (row: T) => string;
  value: (row: T) => number;
  format?: (value: number) => string;
}) {
  const max = Math.max(1, ...rows.map(value));
  if (rows.length === 0) return <p className="empty">No data yet</p>;

  return (
    <div className="bar-list">
      {rows.map((row) => {
        const v = value(row);
        return (
          <div className="bar-row" key={label(row)}>
            <div className="bar-label" title={label(row)}>
              {label(row)}
            </div>
            <div className="bar-track">
              <div className="bar-fill" style={{ width: `${(v / max) * 100}%` }} />
            </div>
            <div className="bar-value">{format(v)}</div>
          </div>
        );
      })}
    </div>
  );
}

function TinySeriesChart({
  rows,
  valueKey,
  label,
}: {
  rows: AnalyticsSeriesRow[];
  valueKey: string;
  label: string;
}) {
  const values = rows.map((row) => Number(row[valueKey] ?? 0));
  const max = Math.max(1, ...values);
  const width = 640;
  const height = 160;
  const pad = { top: 22, right: 12, bottom: 34, left: 36 };
  const innerW = width - pad.left - pad.right;
  const innerH = height - pad.top - pad.bottom;
  const barW = innerW / Math.max(rows.length, 1);

  if (rows.length === 0) return <p className="empty">No time series data yet</p>;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="chart-svg compact">
      <text x={pad.left} y={14} className="chart-label" fontSize={11}>
        {label}
      </text>
      {rows.map((row, i) => {
        const v = Number(row[valueKey] ?? 0);
        const h = (v / max) * innerH;
        const x = pad.left + i * barW + barW * 0.18;
        const y = pad.top + innerH - h;
        return (
          <g key={`${row.bucket}-${i}`}>
            <rect x={x} y={y} width={Math.max(3, barW * 0.64)} height={h} rx={2} className="chart-accent" />
            <text x={x + barW * 0.32} y={height - 10} className="chart-label" fontSize={9} textAnchor="middle">
              {formatBucket(String(row.bucket))}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

function SeriesTable({
  rows,
  columns,
}: {
  rows: AnalyticsSeriesRow[];
  columns: { key: string; label: string; format?: (value: number | string | null | undefined) => string }[];
}) {
  if (rows.length === 0) return <p className="empty">No rows yet</p>;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key}>{col.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={`${row.bucket}-${idx}`}>
              {columns.map((col) => (
                <td key={col.key} className={col.key === "bucket" ? "mono" : undefined}>
                  {col.format
                    ? col.format(row[col.key] as number | string | null | undefined)
                    : formatNum(row[col.key] as number | string | null | undefined)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function LatencyTable({ rows }: { rows: AnalyticsLatencyRow[] }) {
  if (rows.length === 0) return <p className="empty">No latency data yet</p>;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>p50</th>
            {"p75Ms" in rows[0] && <th>p75</th>}
            <th>p90</th>
            <th>p95</th>
            <th>p99</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.name}>
              <td>{row.name}</td>
              <td>{formatNum(row.p50Ms)}</td>
              {"p75Ms" in row && <td>{formatNum(row.p75Ms)}</td>}
              <td>{formatNum(row.p90Ms)}</td>
              <td>{formatNum(row.p95Ms)}</td>
              <td>{formatNum(row.p99Ms)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function LevelSummary({ rows }: { rows: { bucket: string; observationsByLevel: Record<string, number> }[] }) {
  const flattened = rows.map((row) => ({
    bucket: row.bucket,
    levels: Object.entries(row.observationsByLevel)
      .map(([level, count]) => `${level}: ${count}`)
      .join(", "),
  }));
  return (
    <SeriesTable
      rows={flattened}
      columns={[
        { key: "bucket", label: "Time", format: (v) => formatBucket(String(v)) },
        { key: "levels", label: "Observations by level", format: (v) => String(v ?? "—") },
      ]}
    />
  );
}

function ScoreBreakdown({ score }: { score: ScoreAnalytics }) {
  const hasMoving = score.movingAverage.length > 0;
  const categorical = score.categoricalOverTime.map((row) => ({
    bucket: row.bucket,
    counts: Object.entries(row.counts)
      .map(([name, count]) => `${name}: ${count}`)
      .join(", "),
  }));

  return (
    <div className="analytics-grid two">
      <div>
        <div className="subhead">Total aggregate</div>
        {score.histogram.length > 0 ? (
          <BarList rows={score.histogram} label={(r) => r.bucket} value={(r) => r.count} />
        ) : (
          <BarList rows={score.categoricalBreakdown} label={(r) => r.category} value={(r) => r.count} />
        )}
      </div>
      <div>
        <div className="subhead">Over time</div>
        {hasMoving ? (
          <>
            <TinySeriesChart rows={score.movingAverage} valueKey="movingAverage" label="Moving average" />
            <SeriesTable
              rows={score.movingAverage}
              columns={[
                { key: "bucket", label: "Time", format: (v) => formatBucket(String(v)) },
                { key: "movingAverage", label: "Moving avg" },
              ]}
            />
          </>
        ) : (
          <SeriesTable
            rows={categorical}
            columns={[
              { key: "bucket", label: "Time", format: (v) => formatBucket(String(v)) },
              { key: "counts", label: "Category counts", format: (v) => String(v ?? "—") },
            ]}
          />
        )}
      </div>
    </div>
  );
}

export default function Analytics({ analytics }: Props) {
  const [usageTab, setUsageTab] = useState<UsageTab>("costModel");
  const [selectedModel, setSelectedModel] = useState("all");
  const scoreKeys = Object.keys(analytics?.scoreAnalytics ?? {});
  const [selectedScore, setSelectedScore] = useState<string>("");
  const activeScoreKey = selectedScore && scoreKeys.includes(selectedScore) ? selectedScore : scoreKeys[0];
  const activeScore = activeScoreKey ? analytics?.scoreAnalytics[activeScoreKey] : null;

  const usageRows = useMemo(() => {
    if (!analytics) return [];
    const rows =
      usageTab === "costModel"
        ? analytics.modelUsage.costByModel
        : usageTab === "costType"
          ? analytics.modelUsage.costByType
          : usageTab === "usageModel"
            ? analytics.modelUsage.usageByModel
            : analytics.modelUsage.usageByType;
    if (selectedModel === "all" || usageTab === "costType" || usageTab === "usageType") return rows;
    return rows.filter((row) => row.model === selectedModel);
  }, [analytics, selectedModel, usageTab]);

  if (!analytics) return <p className="empty">No analytics available yet</p>;

  const usageValueKey = usageTab === "costModel" || usageTab === "costType" ? "costUsd" : "tokens";
  const usageGroupKey = usageTab === "costModel" || usageTab === "usageModel"
    ? "model"
    : usageTab === "costType"
      ? "costType"
      : "usageType";

  return (
    <div className="analytics-panel">
      <div className="metrics-row">
        <div className="metric-cell">
          <div className="metric-label">Total traces</div>
          <div className="metric-value">{analytics.traces.total}</div>
        </div>
        <div className="metric-cell">
          <div className="metric-label">Total cost</div>
          <div className="metric-value">{formatUsd(analytics.modelCosts.totalCostUsd)}</div>
        </div>
        <div className="metric-cell">
          <div className="metric-label">Total scores</div>
          <div className="metric-value">{analytics.scores.total}</div>
        </div>
      </div>

      <div className="analytics-grid two">
        <div className="panel">
          <div className="panel-header">
            <h2 className="panel-title">Traces by name</h2>
          </div>
          <div className="panel-body">
            <BarList rows={analytics.traces.byName} label={(r) => r.name} value={(r) => r.count} />
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <h2 className="panel-title">User consumption</h2>
          </div>
          <div className="panel-body stacked">
            <div>
              <div className="subhead">Token cost by user</div>
              <BarList
                rows={analytics.userConsumption.costByUser}
                label={(r) => r.user}
                value={(r) => r.totalCostUsd}
                format={formatUsd}
              />
            </div>
            <div>
              <div className="subhead">Trace count by user</div>
              <BarList
                rows={analytics.userConsumption.traceCountByUser}
                label={(r) => r.user}
                value={(r) => r.traceCount}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-header">
          <h2 className="panel-title">Model costs</h2>
        </div>
        <div className="panel-body">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Tokens</th>
                  <th>USD cost</th>
                </tr>
              </thead>
              <tbody>
                {analytics.modelCosts.byModel.map((row) => (
                  <tr key={row.model}>
                    <td>{row.model}</td>
                    <td>{formatNum(row.tokens)}</td>
                    <td>{formatUsd(row.costUsd)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-header">
          <h2 className="panel-title">Scores summary</h2>
          <span className="badge outline">{analytics.scores.total} scores</span>
        </div>
        <div className="panel-body">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Source</th>
                  <th>Type</th>
                  <th>#</th>
                  <th>Avg</th>
                  <th>0s</th>
                  <th>1s</th>
                </tr>
              </thead>
              <tbody>
                {analytics.scores.summary.map((row) => (
                  <tr key={`${row.name}-${row.source}-${row.dataType}`}>
                    <td>{row.name}</td>
                    <td>{row.source}</td>
                    <td>{row.dataType}</td>
                    <td>{row.count}</td>
                    <td>{formatNum(row.average)}</td>
                    <td>{row.zeros ?? 0}</td>
                    <td>{row.ones ?? 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="analytics-grid two">
        <div className="panel">
          <div className="panel-header">
            <h2 className="panel-title">Traces / observations over time</h2>
            <span className="badge outline">v1</span>
          </div>
          <div className="panel-body">
            <TinySeriesChart rows={analytics.timeSeries.traceObservationByLevel} valueKey="traceCount" label="Trace count" />
            <SeriesTable
              rows={analytics.timeSeries.traceObservationByLevel}
              columns={[
                { key: "bucket", label: "Time", format: (v) => formatBucket(String(v)) },
                { key: "traceCount", label: "Traces" },
                { key: "observationCount", label: "Observations" },
              ]}
            />
          </div>
        </div>
        <div className="panel">
          <div className="panel-header">
            <h2 className="panel-title">Observations by level</h2>
            <span className="badge outline">events beta</span>
          </div>
          <div className="panel-body">
            <LevelSummary rows={analytics.timeSeries.observationsByLevel} />
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-header usage-header">
          <h2 className="panel-title">Model usage</h2>
          <select className="select" value={selectedModel} onChange={(e) => setSelectedModel(e.target.value)}>
            <option value="all">All models</option>
            {analytics.modelUsage.models.map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
          </select>
        </div>
        <div className="panel-body">
          <div className="mini-tabs">
            {USAGE_TABS.map((tab) => (
              <button
                key={tab.id}
                type="button"
                className={`mini-tab ${usageTab === tab.id ? "active" : ""}`}
                onClick={() => setUsageTab(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>
          <TinySeriesChart
            rows={usageRows}
            valueKey={usageValueKey}
            label={usageValueKey === "costUsd" ? "USD over time" : "Tokens over time"}
          />
          <SeriesTable
            rows={usageRows}
            columns={[
              { key: "bucket", label: "Time", format: (v) => formatBucket(String(v)) },
              { key: usageGroupKey, label: usageGroupKey },
              {
                key: usageValueKey,
                label: usageValueKey === "costUsd" ? "USD" : "Tokens",
                format: usageValueKey === "costUsd" ? (v) => formatUsd(Number(v ?? 0)) : undefined,
              },
            ]}
          />
        </div>
      </div>

      <div className="analytics-grid three">
        <div className="panel">
          <div className="panel-header">
            <h2 className="panel-title">Trace latency percentiles</h2>
          </div>
          <div className="panel-body">
            <LatencyTable rows={analytics.latencies.trace} />
          </div>
        </div>
        <div className="panel">
          <div className="panel-header">
            <h2 className="panel-title">Generation latency percentiles</h2>
          </div>
          <div className="panel-body">
            <LatencyTable rows={analytics.latencies.generation} />
          </div>
        </div>
        <div className="panel">
          <div className="panel-header">
            <h2 className="panel-title">Observation latency percentiles</h2>
          </div>
          <div className="panel-body">
            <LatencyTable rows={analytics.latencies.observation} />
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-header">
          <h2 className="panel-title">Model latencies</h2>
        </div>
        <div className="panel-body">
          <SeriesTable
            rows={analytics.modelLatencies.series}
            columns={[
              { key: "bucket", label: "Time", format: (v) => formatBucket(String(v)) },
              { key: "model", label: "Model" },
              { key: "p50Ms", label: "p50" },
              { key: "p75Ms", label: "p75" },
              { key: "p90Ms", label: "p90" },
              { key: "p95Ms", label: "p95" },
              { key: "p99Ms", label: "p99" },
            ]}
          />
        </div>
      </div>

      <div className="panel">
        <div className="panel-header usage-header">
          <h2 className="panel-title">Scores analytics</h2>
          {scoreKeys.length > 0 && (
            <select className="select" value={activeScoreKey ?? ""} onChange={(e) => setSelectedScore(e.target.value)}>
              {scoreKeys.map((key) => (
                <option key={key} value={key}>
                  {key}
                </option>
              ))}
            </select>
          )}
        </div>
        <div className="panel-body">
          {activeScore ? <ScoreBreakdown score={activeScore} /> : <p className="empty">No score analytics yet</p>}
        </div>
      </div>
    </div>
  );
}
