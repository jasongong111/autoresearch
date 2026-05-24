import type { Iteration } from "./types";

interface Props {
  iterations: Iteration[];
}

function chipClass(outcome: string): string {
  if (outcome === "success") return "chip success";
  if (outcome === "failure") return "chip failure";
  return "chip neutral";
}

export default function IterationTable({ iterations }: Props) {
  if (iterations.length === 0) {
    return <p className="empty">No iterations logged</p>;
  }

  const rawKeys = new Set<string>();
  iterations.forEach((it) => Object.keys(it.raw).forEach((k) => rawKeys.add(k)));
  const extraCols = [...rawKeys].filter(
    (k) => !["iteration", "round", "status", "description", "commit", "metric", "delta"].includes(k)
  );

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Status</th>
            <th>Outcome</th>
            <th>Value</th>
            <th>Description</th>
            {extraCols.slice(0, 4).map((c) => (
              <th key={c}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {[...iterations].reverse().map((it, i) => (
            <tr key={`${it.index}-${i}`}>
              <td className="mono">{it.index}</td>
              <td>{it.status || "—"}</td>
              <td>
                <span className={chipClass(it.outcome)}>{it.outcome}</span>
              </td>
              <td>
                {it.primaryValue != null ? `${it.primaryValue}` : "—"}
                {it.primaryLabel ? ` (${it.primaryLabel})` : ""}
              </td>
              <td>{it.description || it.location || "—"}</td>
              {extraCols.slice(0, 4).map((c) => (
                <td key={c}>{it.raw[c] || "—"}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
