import { backendFetch, type EntityGraph } from "@/lib/backend";
import { SectionHeader, WorkspaceShell } from "../ui/workspace-shell";

export default async function GraphPage() {
  const graph = await backendFetch<EntityGraph>("/graph").catch(() => ({ nodes: [], edges: [] }));
  const cases = graph.nodes.filter(node => node.kind === "case");
  return <WorkspaceShell><div className="content section-page"><SectionHeader eyebrow="RELATIONSHIP INTELLIGENCE" title="Entity graph" description="Trace relationships between cases and their evidence records."/><section className="panel graph-canvas">{cases.map(item => { const evidence = graph.edges.filter(edge => edge.source === item.id).map(edge => graph.nodes.find(node => node.id === edge.target)).filter(Boolean); return <div className="graph-cluster" key={item.id}><div className={`graph-node case-node ${item.risk >= 80 ? "hot" : ""}`}><strong>{item.label}</strong><span>{item.id} · risk {item.risk}</span></div><div className="graph-line"/><div className="graph-evidence">{evidence.map(node => node && <div className="graph-node" key={node.id}><strong>{node.label}</strong><span>{node.kind}</span></div>)}</div></div>})}{!cases.length && <div className="empty-state">The graph will populate as cases and evidence are added.</div>}</section></div></WorkspaceShell>;
}

