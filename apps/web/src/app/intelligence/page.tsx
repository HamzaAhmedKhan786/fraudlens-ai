import { backendFetch, type PublicIntelligence } from "@/lib/backend";
import { IntelligenceConsole } from "./intelligence-console";
import { SectionHeader, WorkspaceShell } from "../ui/workspace-shell";

export default async function IntelligencePage() {
  const items = await backendFetch<PublicIntelligence[]>("/intelligence/public").catch(() => []);
  return <WorkspaceShell><div className="content section-page"><SectionHeader eyebrow="VERIFIABLE SOURCES" title="Public intelligence" description="Live public facts with explicit provenance—never hardcoded fraud labels."/><IntelligenceConsole initialItems={items}/></div></WorkspaceShell>;
}
