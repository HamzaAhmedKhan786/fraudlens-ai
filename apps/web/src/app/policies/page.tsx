import { backendFetch, type PolicyDefinition } from "@/lib/backend";
import { PolicyConsole } from "../ui/policy-console";
import { SectionHeader, WorkspaceShell } from "../ui/workspace-shell";

export default async function PoliciesPage() {
  const policies = await backendFetch<PolicyDefinition[]>("/policies").catch(() => []);
  return <WorkspaceShell><div className="content section-page"><SectionHeader eyebrow="GOVERNANCE" title="Detection policies" description="Versioned, persisted controls with audited administrative changes."/><PolicyConsole initial={policies}/></div></WorkspaceShell>;
}
