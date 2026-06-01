import type { Iteration } from "../types";

interface Props {
  command: string;
  iterations: Iteration[];
}

function groupByRound(iterations: Iteration[]): Map<number, Iteration[]> {
  const m = new Map<number, Iteration[]>();
  for (const it of iterations) {
    const list = m.get(it.index) ?? [];
    list.push(it);
    m.set(it.index, list);
  }
  return m;
}

export default function MetricChart({ command, iterations }: Props) {
  if (iterations.length === 0) {
    return <p className="empty">No iterations yet</p>;
  }

  const width = 600;
  const height = 180;
  const pad = { top: 20, right: 20, bottom: 30, left: 44 };
  const innerW = width - pad.left - pad.right;
  const innerH = height - pad.top - pad.bottom;

  if (command === "security") {
    const byIndex = groupByRound(iterations);
    const indices = [...byIndex.keys()].sort((a, b) => a - b);
    const maxCount = Math.max(1, ...indices.map((i) => byIndex.get(i)!.length));
    const barW = innerW / Math.max(indices.length, 1);

    return (
      <svg viewBox={`0 0 ${width} ${height}`} className="chart-svg">
        {indices.map((idx, i) => {
          const count = byIndex.get(idx)!.length;
          const h = (count / maxCount) * innerH;
          const x = pad.left + i * barW + barW * 0.15;
          const y = pad.top + innerH - h;
          return (
            <g key={idx}>
              <rect
                x={x}
                y={y}
                width={barW * 0.7}
                height={h}
                className="chart-error"
                opacity={0.85}
                rx={2}
              />
              <text
                x={x + barW * 0.35}
                y={height - 8}
                className="chart-label"
                fontSize={10}
                textAnchor="middle"
              >
                {idx}
              </text>
            </g>
          );
        })}
        <text x={pad.left} y={14} className="chart-label" fontSize={11}>
          Findings per iteration
        </text>
      </svg>
    );
  }

  if (command === "predict" || command === "reason") {
    const byRound = groupByRound(iterations);
    const rounds = [...byRound.keys()].sort((a, b) => a - b);
    const values = rounds.map((r) => {
      const rows = byRound.get(r)!;
      return rows.reduce((s, it) => s + (it.primaryValue ?? 0), 0) / rows.length;
    });
    const maxV = Math.max(1, ...values.map(Math.abs));
    const barW = innerW / Math.max(rounds.length, 1);

    return (
      <svg viewBox={`0 0 ${width} ${height}`} className="chart-svg">
        {rounds.map((r, i) => {
          const v = values[i];
          const h = (Math.abs(v) / maxV) * innerH;
          const x = pad.left + i * barW + barW * 0.15;
          const y = pad.top + innerH - h;
          return (
            <g key={r}>
              <rect x={x} y={y} width={barW * 0.7} height={h} className="chart-accent" rx={2} />
              <text
                x={x + barW * 0.35}
                y={height - 8}
                className="chart-label"
                fontSize={10}
                textAnchor="middle"
              >
                R{r}
              </text>
            </g>
          );
        })}
        <text x={pad.left} y={14} className="chart-label" fontSize={11}>
          Activity by round
        </text>
      </svg>
    );
  }

  const points = iterations.filter((it) => it.primaryValue != null);
  if (points.length === 0) {
    return <p className="empty">No numeric metric in this run</p>;
  }

  const vals = points.map((p) => p.primaryValue as number);
  const minV = Math.min(...vals);
  const maxV = Math.max(...vals);
  const range = maxV - minV || 1;

  const coords = points.map((p, i) => {
    const x = pad.left + (i / Math.max(points.length - 1, 1)) * innerW;
    const y = pad.top + innerH - ((p.primaryValue! - minV) / range) * innerH;
    return { x, y, p };
  });

  const linePath = coords.map((c, i) => `${i === 0 ? "M" : "L"}${c.x},${c.y}`).join(" ");

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="chart-svg">
      <path d={linePath} fill="none" className="chart-line" strokeWidth={2} />
      {coords.map((c) => (
        <circle
          key={`${c.p.index}-${c.p.status}`}
          cx={c.x}
          cy={c.y}
          r={4}
          className={
            c.p.outcome === "success"
              ? "chart-success"
              : c.p.outcome === "failure"
                ? "chart-error"
                : "chart-muted"
          }
        />
      ))}
      <text x={pad.left} y={14} className="chart-label" fontSize={11}>
        {points[0]?.primaryLabel ?? "metric"} over iterations
      </text>
    </svg>
  );
}
