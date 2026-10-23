import { WorkspaceShell } from "./ui/workspace-shell";
export default function Loading() {
  return <WorkspaceShell><div className="content" role="status" aria-label="Loading workspace"><div className="skeleton skeleton-title"/><div className="kpi-grid">{Array.from({ length: 5 }, (_, i) => <div className="panel skeleton skeleton-kpi" key={i}/>)}</div><div className="panel skeleton skeleton-chart"/><span className="sr-only">Loading workspace data…</span></div></WorkspaceShell>;
}
