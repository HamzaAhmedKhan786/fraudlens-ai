import { SectionHeader, WorkspaceShell } from "../ui/workspace-shell";

const roles = [
  ["Hamza Khan", "Administrator", "Full workspace administration", "ACTIVE"],
  ["Fraud Operations", "Senior Analyst", "Investigate and decide cases", "ACTIVE"],
  ["Compliance Review", "Reviewer", "Read, comment, and approve", "ACTIVE"],
  ["Automation Service", "Service account", "Evidence ingestion and orchestration", "RESTRICTED"],
];
export default function TeamPage() {
  return <WorkspaceShell><div className="content section-page"><SectionHeader eyebrow="ACCESS CONTROL" title="Team & access" description="Role-based access model for analysts, reviewers, administrators, and services."/><section className="panel data-panel"><div className="records"><div className="record team-record record-head"><span>Principal</span><span>Role</span><span>Permissions</span><span>Status</span></div>{roles.map(([name,role,permissions,state]) => <div className="record team-record" key={name}><strong>{name}</strong><span>{role}</span><span>{permissions}</span><span className="status-pill enabled">{state}</span></div>)}</div></section><div className="notice-box">Production identity should be connected through OIDC/SAML. The current API-key boundary is intended for service-to-service development access.</div></div></WorkspaceShell>;
}

