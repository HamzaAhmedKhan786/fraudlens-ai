import { backendFetch, type CaseSummary, type GmailConnection, type ProviderCapability } from "@/lib/backend";
import { SectionHeader, WorkspaceShell } from "../ui/workspace-shell";
import { GmailConsole } from "./gmail-console";

const disconnected: GmailConnection = { connected: false, email_address: null, status: "NOT_CONNECTED", scopes: [], connected_at: null, last_sync_at: null, last_error: null };

export default async function ConnectorsPage() {
  const [connection, cases, capabilities] = await Promise.all([
    backendFetch<GmailConnection>("/connectors/google").catch(() => disconnected),
    backendFetch<CaseSummary[]>("/cases").catch(() => []),
    backendFetch<ProviderCapability[]>("/connectors/email/capabilities").catch(() => []),
  ]);
  const microsoft=capabilities.find(item=>item.provider==="microsoft");
  return <WorkspaceShell><div className="content section-page"><SectionHeader eyebrow="AUTHORIZED SOURCES" title="Email connectors" description="Provider-neutral, consented evidence ingestion with explicit filters, audit history, deduplication, and retention."/><GmailConsole initial={connection} cases={cases}/><section className="panel data-panel"><div className="panel-head"><div><h2>Microsoft 365 / Outlook</h2><p>{microsoft?.detail??"Provider capability unavailable."}</p></div><span className="status-pill">{microsoft?.status??"UNAVAILABLE"}</span></div><div className="panel-body"><p>Prepared modes: {microsoft?.modes.join(", ")??"none"}. Entra ID credentials, Graph permissions, and tenant admin consent are required before connection.</p><button disabled>Connect Microsoft 365</button></div></section></div></WorkspaceShell>;
}
