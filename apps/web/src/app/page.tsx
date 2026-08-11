import {
  Activity, Bell, ChevronDown, CircleUserRound, FileWarning, Gauge, GitBranch,
  LayoutDashboard, ListFilter, Search, Settings, ShieldCheck, Sparkles, UploadCloud, Users, Workflow,
} from "lucide-react";
import Link from "next/link";
import { getDashboard, type DashboardMetrics } from "@/lib/backend";
import { NewInvestigationButton } from "./ui/new-investigation";

const fallback: DashboardMetrics = {
  open_cases: 0, critical_cases: 0, high_risk_cases: 0, completed_investigations: 0,
  average_risk: 0, agent_confidence: 0, priority_cases: [],
};

const agents = [
  ["Email security", "Reply-To and authentication", "3 findings", "done"],
  ["Document integrity", "IBAN and metadata analysis", "2 findings", "done"],
  ["URL reputation", "Domain age and redirect chain", "1 finding", "done"],
  ["AI investigator", "Evidence-grounded synthesis", "Running", "active"],
];

const navPaths: Record<string, string> = { Overview: "/", Cases: "/cases", "Evidence intake": "/uploads", Investigations: "/investigations", "Entity graph": "/graph", "Agent activity": "/agents", "Detection policies": "/policies", "Model health": "/models", "Team & access": "/team", Settings: "/settings" };
function NavItem({ icon: Icon, label, active = false }: { icon: typeof Gauge; label: string; active?: boolean }) {
  return <Link href={navPaths[label] ?? "/"} className={`nav-item ${active ? "active" : ""}`}><Icon size={18} /><span>{label}</span></Link>;
}

export default async function Dashboard() {
  const dashboard = await getDashboard().catch(() => fallback);
  const cases = dashboard.priority_cases.map((item) => ({
    id: item.id, subject: item.subject, type: item.case_type, score: item.risk_score,
    level: item.severity[0] + item.severity.slice(1).toLowerCase(), age: item.status.replaceAll("_", " "),
  }));
  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand"><img src="/brand/app-icon.png" alt="" /><div><strong>FraudLens</strong><span>AI</span></div></div>
        <div className="workspace"><span>Workspace</span><button>Acme Financial <ChevronDown size={14} /></button></div>
        <nav>
          <p>OPERATIONS</p>
          <NavItem icon={LayoutDashboard} label="Overview" active />
          <NavItem icon={FileWarning} label="Cases" />
          <NavItem icon={UploadCloud} label="Evidence intake" />
          <NavItem icon={Workflow} label="Investigations" />
          <NavItem icon={GitBranch} label="Entity graph" />
          <p>INTELLIGENCE</p>
          <NavItem icon={Sparkles} label="Agent activity" />
          <NavItem icon={ShieldCheck} label="Detection policies" />
          <NavItem icon={Activity} label="Model health" />
          <p>ADMIN</p>
          <NavItem icon={Users} label="Team & access" />
          <NavItem icon={Settings} label="Settings" />
        </nav>
        <div className="system-state"><i /><div><strong>All systems operational</strong><span>12 agents online</span></div></div>
      </aside>

      <section className="workspace-main">
        <header className="topbar">
          <div className="search"><Search size={17} /><span>Search cases, entities, evidence...</span><kbd>⌘ K</kbd></div>
          <button className="icon-button"><Bell size={18} /><i /></button>
          <button className="profile"><span>HK</span><div><strong>Hamza Khan</strong><small>Administrator</small></div><ChevronDown size={14} /></button>
        </header>

        <div className="content">
          <div className="heading-row"><div><p className="eyebrow">COMMAND CENTER</p><h1>Fraud operations overview</h1><p>Monitor risk, investigations, and agent performance across your organization.</p></div><NewInvestigationButton /></div>

          <section className="metrics">
            <article><span>OPEN CASES</span><div><strong>{dashboard.open_cases}</strong><em className="up">Live</em></div><p><b style={{width:"68%"}} />Persisted case queue</p></article>
            <article><span>CRITICAL RISK</span><div><strong>{dashboard.critical_cases}</strong><em className="danger">{dashboard.high_risk_cases} high+</em></div><p><b className="red" style={{width:"38%"}} />Requires immediate action</p></article>
            <article><span>AVERAGE RISK</span><div><strong>{dashboard.average_risk}</strong><em className="up">/100</em></div><p><b style={{width:`${dashboard.average_risk}%`}} />Across active cases</p></article>
            <article><span>AGENT CONFIDENCE</span><div><strong>{dashboard.agent_confidence}%</strong><em className="up">Audited</em></div><p><b style={{width:`${dashboard.agent_confidence}%`}} />{dashboard.completed_investigations} completed runs</p></article>
          </section>

          <div className="grid-main">
            <section className="panel cases-panel">
              <div className="panel-head"><div><h2>Priority cases</h2><p>Ranked by deterministic risk score</p></div><button><ListFilter size={15} /> Filter</button></div>
              <div className="table-head"><span>CASE</span><span>SUBJECT</span><span>TYPE</span><span>RISK</span><span>AGE</span></div>
              {cases.map((item) => <div className="case-row" key={item.id}>
                <span className="case-id">{item.id}</span><span><strong>{item.subject}</strong><small>Automated triage complete</small></span><span>{item.type}</span><span className="risk"><i className={item.level.toLowerCase()}>{item.score}</i><b>{item.level}</b></span><span>{item.age}</span>
              </div>)}
              <Link className="view-all" href="/cases">View all cases →</Link>
            </section>

            <aside className="panel agent-panel">
              <div className="panel-head"><div><h2>Live investigation</h2><p>FR-29482 · 4 agents</p></div><span className="live"><i /> LIVE</span></div>
              <div className="risk-hero"><div className="risk-ring"><strong>92</strong><span>/100</span></div><div><span>OVERALL RISK</span><strong>Critical</strong><p>High-confidence fraud pattern</p></div></div>
              <div className="agent-list">{agents.map(([name, detail, result, state]) => <div className="agent" key={name}><span className={state}><ShieldCheck size={16} /></span><div><strong>{name}</strong><small>{detail}</small></div><b>{result}</b></div>)}</div>
              <Link className="open-case" href="/investigations">Open investigation <span>→</span></Link>
            </aside>
          </div>

          <section className="panel signals">
            <div className="panel-head"><div><h2>Detection signals</h2><p>Risk distribution across active cases</p></div><button>Last 7 days <ChevronDown size={14} /></button></div>
            <div className="signal-grid">
              {[['Email compromise','34%','+8%'],['Document tampering','26%','+3%'],['Identity fraud','18%','−2%'],['Deepfake media','12%','+5%'],['Malicious URL','10%','−1%']].map(([name,value,delta], i)=><div key={name}><span><i className={`signal s${i}`} />{name}</span><strong>{value}</strong><em>{delta}</em><b><i style={{width:value}} /></b></div>)}
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}
