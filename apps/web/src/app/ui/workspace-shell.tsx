"use client";

import {
  Activity, ArrowUpRight, BookOpen, ChevronDown, FileWarning, GitBranch, Globe2,
  LayoutDashboard, Mail, Menu, Search, Settings, ShieldCheck, Sparkles,
  UploadCloud, Users, Workflow, X, CreditCard, ScrollText, CircleHelp,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import type { SessionInfo } from "@/lib/analytics-types";
import { WorkspaceSwitcher } from "./workspace-switcher";

const sections = [
  { group: "Operations", items: [
    ["/", "Command center", LayoutDashboard], ["/investigations", "Investigations", Workflow],
    ["/cases", "Cases", FileWarning], ["/uploads", "Evidence intake", UploadCloud],
    ["/connectors", "Email connectors", Mail], ["/reviews", "Review queue", ShieldCheck],
  ] },
  { group: "Intelligence", items: [
    ["/analytics", "Risk analytics", Activity], ["/intelligence", "Public intelligence", Globe2],
    ["/graph", "Entity graph", GitBranch], ["/agents", "AI agents", Sparkles],
    ["/policies", "Detection policies", ShieldCheck], ["/models", "Model health", Activity],
  ] },
  { group: "Management", items: [
    ["/workspaces", "Workspaces", Users], ["/team", "Team & permissions", Users],
    ["/billing", "Subscription & billing", CreditCard], ["/audit", "Audit logs", ScrollText],
    ["/trash", "Deleted investigations", FileWarning], ["/settings", "Settings", Settings],
  ] },
] as const;

export function openGuide() { window.dispatchEvent(new Event("fraudlens:help")); }

export function WorkspaceShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [mobile, setMobile] = useState(false);
  const navigation = useRef<HTMLElement>(null);
  const menuToggle = useRef<HTMLButtonElement>(null);
  const [collapsed, setCollapsed] = useState<string[]>([]);
  const [session, setSession] = useState<SessionInfo | null>(null);
  const [profileOpen, setProfileOpen] = useState(false);
  useEffect(() => {
    const media = window.matchMedia("(max-width: 760px)");
    const update = () => { setMobile(media.matches); if (!media.matches) setMobileOpen(false); };
    update(); media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);
  useEffect(() => {
    if (!mobile || !mobileOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    navigation.current?.querySelector<HTMLButtonElement>(".mobile-nav-close")?.focus();
    const keyboard = (event: KeyboardEvent) => {
      if (event.key === "Escape") { event.preventDefault(); setMobileOpen(false); return; }
      if (event.key !== "Tab") return;
      const controls = Array.from(navigation.current?.querySelectorAll<HTMLElement>(
        "a[href],button:not(:disabled),select:not(:disabled)",
      ) ?? []).filter(element => element.getClientRects().length > 0);
      const first = controls[0], last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    };
    document.addEventListener("keydown", keyboard);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", keyboard);
      menuToggle.current?.focus();
    };
  }, [mobile, mobileOpen]);
  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/session", { signal: controller.signal }).then(r => r.ok ? r.json() : null)
      .then(setSession).catch(() => {});
    return () => controller.abort();
  }, []);
  const section = sections.flatMap(group => [...group.items]).find(([href]) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href));
  return <div className={`app-shell ${mobileOpen ? "navigation-open" : ""}`}>
    <a className="skip-link" href="#workspace-content">Skip to content</a>
    {mobileOpen && <button className="nav-scrim" aria-label="Close navigation" onClick={() => setMobileOpen(false)}/>}
    <aside ref={navigation} className="sidebar" aria-label="Main navigation" aria-hidden={mobile && !mobileOpen || undefined} inert={mobile && !mobileOpen || undefined}>
      <button className="mobile-nav-close" aria-label="Close navigation panel" onClick={() => setMobileOpen(false)}><X size={18}/></button>
      <Link href="/" className="brand"><img src="/brand/app-icon.png" alt=""/><div><strong>FraudLens</strong><span>AI</span></div><small>INTELLIGENCE</small></Link>
      <WorkspaceSwitcher />
      <nav>{sections.map(group => <div className="nav-group" key={group.group}>
        <button className="nav-group-label" onClick={() => setCollapsed(current => current.includes(group.group) ? current.filter(x => x !== group.group) : [...current, group.group])} aria-expanded={!collapsed.includes(group.group)}>{group.group}<ChevronDown size={12}/></button>
        {!collapsed.includes(group.group) && group.items.map(([href, label, Icon]) =>
          <Link key={href} title={label} href={href} onClick={() => setMobileOpen(false)} aria-current={pathname === href ? "page" : undefined} className={`nav-item ${pathname === href || (href !== "/" && pathname.startsWith(href)) ? "active" : ""}`}><Icon size={16}/><span>{label}</span>{pathname === href && <i/>}</Link>)}
      </div>)}</nav>
      <button className="sidebar-assistant" onClick={openGuide}><span className="assistant-symbol"><Sparkles size={20}/></span><div><strong>AI help & documentation</strong><small>Answers from your product guide</small></div><ArrowUpRight size={15}/></button>
      <Link className="system-state" href="/models"><ShieldCheck size={15}/><div><strong>Configuration & readiness</strong><span>View available capabilities</span></div><ArrowUpRight size={13}/></Link>
    </aside>
    <div className="workspace-main" inert={mobile && mobileOpen || undefined}>
      <header className="topbar">
        <button ref={menuToggle} className="icon-button mobile-menu" aria-label={mobileOpen ? "Close navigation" : "Open navigation"} onClick={() => setMobileOpen(value => !value)}>{mobileOpen ? <X size={20}/> : <Menu size={20}/>}</button>
        <div className="topbar-breadcrumb"><ShieldCheck size={15}/><span>Workspace</span><span>/</span><strong>{section?.[1] ?? "Investigation"}</strong></div>
        <form className="global-search" action="/cases"><Search size={15}/><input name="q" aria-label="Search cases" placeholder="Search cases, subjects…"/><kbd>↵</kbd></form>
        <button className="icon-button" aria-label="Open help" onClick={openGuide}><CircleHelp size={18}/></button>
        <div className="profile-container"><button className="profile" aria-expanded={profileOpen} onClick={() => setProfileOpen(value => !value)}><span>{session?.name.slice(0, 2).toUpperCase() ?? "FL"}</span><div><strong>{session?.development ? "Development workspace" : session?.name ?? "Workspace session"}</strong><small>{session?.development ? "Local service access" : session?.roles.join(" · ") ?? "Loading identity…"}</small></div><ChevronDown size={13}/></button>
          {profileOpen && <div className="profile-menu"><Link href="/workspaces">Manage workspaces</Link><Link href="/settings">Workspace settings</Link><Link href="/billing">Plan & usage</Link><a href="/api/auth/logout">Sign out</a></div>}
        </div>
      </header>
      <main id="workspace-content" tabIndex={-1}>{children}</main>
      <footer className="workspace-footer"><span>FraudLens AI <i/> Fraud intelligence, explained.</span><button onClick={openGuide}><BookOpen size={13}/> Help center</button></footer>
    </div>
  </div>;
}

export function SectionHeader({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: React.ReactNode }) {
  return <div className="heading-row"><div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p>{description}</p></div>{action}</div>;
}
