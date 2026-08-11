import { backendFetch, type AgentStatus } from "@/lib/backend";
import { SectionHeader, WorkspaceShell } from "../ui/workspace-shell";

export default async function AgentsPage() {
  const agents = await backendFetch<AgentStatus[]>("/agents").catch(() => []);
  return <WorkspaceShell><div className="content section-page"><SectionHeader eyebrow="AGENT CONTROL PLANE" title="Agent activity" description="Capabilities, execution modes, and operational state for every registered agent."/><div className="cards-grid">{agents.map(agent => <article className="panel feature-card" key={agent.id}><div className="feature-top"><span className={`status-dot ${agent.status.toLowerCase()}`}/><em>{agent.status}</em><b>{agent.mode}</b></div><h2>{agent.name}</h2><p>{agent.description}</p><div className="tags">{agent.supported_kinds.map(kind => <span key={kind}>{kind}</span>)}</div><small>{agent.category}</small></article>)}</div></div></WorkspaceShell>;
}
