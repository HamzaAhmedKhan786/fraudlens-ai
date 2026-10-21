import { SectionHeader, WorkspaceShell } from "../ui/workspace-shell";
import { backendFetch, type Member } from "@/lib/backend";

const roles = [
  ["Hamza Khan", "Administrator", "Full workspace administration", "ACTIVE"],
  ["Fraud Operations", "Senior Analyst", "Investigate and decide cases", "ACTIVE"],
  ["Compliance Review", "Reviewer", "Read, comment, and approve", "ACTIVE"],
  ["Automation Service", "Service account", "Evidence ingestion and orchestration", "RESTRICTED"],
];
export default async function TeamPage() {
  const members = await backendFetch<Member[]>("/members").catch(()=>[]);
  return <WorkspaceShell><div className="content section-page"><SectionHeader eyebrow="ACCESS CONTROL" title="Team & access" description="Tenant-isolated memberships and role-based access for administrators, analysts, reviewers, executives, and viewers."/><section className="panel data-panel"><div className="records"><div className="record team-record record-head"><span>Principal</span><span>Role</span><span>Identity</span><span>Status</span></div>{members.map(member => <div className="record team-record" key={member.id}><strong>{member.email}</strong><span>{member.role}</span><span>{member.subject}</span><span className="status-pill enabled">{member.status}</span></div>)}{!members.length&&roles.slice(0,1).map(([name,role,permissions,state]) => <div className="record team-record" key={name}><strong>{name}</strong><span>{role}</span><span>{permissions}</span><span className="status-pill">LOCAL DEVELOPMENT</span></div>)}</div></section><div className="notice-box">OIDC/JWKS validation, organization invitations, and backend role enforcement are available. Configure an identity provider before production; no email passwords are collected.</div></div></WorkspaceShell>;
}

