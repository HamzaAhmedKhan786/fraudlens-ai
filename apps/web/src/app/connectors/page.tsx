import { backendFetch, type GmailConnection } from "@/lib/backend";
import { SectionHeader, WorkspaceShell } from "../ui/workspace-shell";
import { GmailConsole } from "./gmail-console";

const disconnected: GmailConnection = { connected: false, email_address: null, status: "NOT_CONNECTED", scopes: [], connected_at: null, last_sync_at: null, last_error: null };

export default async function ConnectorsPage() {
  const connection = await backendFetch<GmailConnection>("/connectors/google").catch(() => disconnected);
  return <WorkspaceShell><div className="content section-page"><SectionHeader eyebrow="AUTHORIZED SOURCES" title="Email connectors" description="Import user-authorized evidence with explicit filters, audit history, deduplication, and retention."/><GmailConsole initial={connection}/></div></WorkspaceShell>;
}
