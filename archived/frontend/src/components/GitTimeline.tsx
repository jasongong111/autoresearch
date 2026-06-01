import type { GitCommit } from "../types";

interface Props {
  commits: GitCommit[];
}

export default function GitTimeline({ commits }: Props) {
  if (commits.length === 0) {
    return <p className="empty">No experiment: commits found</p>;
  }

  return (
    <ul className="git-list">
      {commits.map((c) => (
        <li key={c.hash}>
          <div className="hash">{c.shortHash}</div>
          <div className="msg">{c.message}</div>
          <div className="date">{c.date}</div>
        </li>
      ))}
    </ul>
  );
}
