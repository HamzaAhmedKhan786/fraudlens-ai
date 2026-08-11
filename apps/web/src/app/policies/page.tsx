import { backendFetch, type PolicyDefinition } from "@/lib/backend";
import { SectionHeader, WorkspaceShell } from "../ui/workspace-shell";

export default async function PoliciesPage() {
  const policies = await backendFetch<PolicyDefinition[]>("/policies").catch(() => []);
  return <WorkspaceShell><div className="content section-page"><SectionHeader eyebrow="GOVERNANCE" title="Detection policies" description="Versioned controls that determine escalation without delegating verdicts to an LLM."/><section className="panel data-panel"><div className="records"><div className="record policy-record record-head"><span>Policy</span><span>Version</span><span>Threshold</span><span>State</span></div>{policies.map(policy => <div className="record policy-record" key={policy.id}><span><strong>{policy.name}</strong><small>{policy.description}</small></span><span>{policy.version}</span><span>{policy.threshold}%</span><span className={`status-pill ${policy.enabled ? "enabled" : ""}`}>{policy.enabled ? "ENABLED" : "DISABLED"}</span></div>)}</div></section></div></WorkspaceShell>;
}

