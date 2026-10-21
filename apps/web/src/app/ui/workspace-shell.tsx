"use client";

import {
  Activity, Bell, ChevronDown, FileWarning, GitBranch, Globe2, LayoutDashboard, Mail,
  Search, Settings, ShieldCheck, Sparkles, UploadCloud, Users, Workflow,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { WorkspaceSwitcher } from "./workspace-switcher";

const sections = [
  { group: "OPERATIONS", items: [
    ["/", "Overview", LayoutDashboard], ["/cases", "Cases", FileWarning],
    ["/uploads", "Evidence intake", UploadCloud],
    ["/investigations", "Investigations", Workflow], ["/graph", "Entity graph", GitBranch],
    ["/reviews", "Review queue", ShieldCheck],
  ] },
  { group: "INTELLIGENCE", items: [
    ["/intelligence", "Public intelligence", Globe2], ["/connectors", "Email connectors", Mail], ["/agents", "Agent activity", Sparkles], ["/policies", "Detection policies", ShieldCheck],
    ["/models", "Model health", Activity],
  ] },
  { group: "ADMIN", items: [
    ["/workspaces", "Workspaces", Users], ["/team", "Team & access", Users], ["/billing", "Plan & usage", FileWarning], ["/trash", "Deleted investigations", FileWarning], ["/settings", "Settings", Settings],
    ["/audit", "Audit trail", FileWarning],
  ] },
] as const;

export function WorkspaceShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return <main className="app-shell">
    <aside className="sidebar">
      <Link href="/" className="brand"><img src="/brand/app-icon.png" alt="" /><div><strong>FraudLens</strong><span>AI</span></div></Link>
      <WorkspaceSwitcher />
      <nav>{sections.map(section => <div key={section.group}><p>{section.group}</p>{section.items.map(([href,label,Icon]) => <Link key={href} href={href} className={`nav-item ${pathname === href || (href !== "/" && pathname.startsWith(href)) ? "active" : ""}`}><Icon size={18}/><span>{label}</span></Link>)}</div>)}</nav>
      <div className="system-state"><i /><div><strong>All systems operational</strong><span>Core agents online</span></div></div>
    </aside>
    <section className="workspace-main">
      <header className="topbar"><div className="search"><Search size={17}/><span>Search cases, entities, evidence...</span><kbd>⌘ K</kbd></div><button className="icon-button" aria-label="Notifications"><Bell size={18}/><i /></button><button className="profile"><span>HK</span><div><strong>Hamza Khan</strong><small>Administrator</small></div><ChevronDown size={14}/></button></header>
      {children}
    </section>
  </main>;
}

export function SectionHeader({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: React.ReactNode }) {
  return <div className="heading-row"><div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p>{description}</p></div>{action}</div>;
}

