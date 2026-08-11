import { backendFetch, type CaseSummary } from "@/lib/backend";
import { CasesTable } from "../ui/cases-table";
import { SectionHeader, WorkspaceShell } from "../ui/workspace-shell";
import { NewInvestigationButton } from "../ui/new-investigation";

export default async function CasesPage() {
  const cases = await backendFetch<CaseSummary[]>("/cases").catch(() => []);
  return <WorkspaceShell><div className="content section-page"><SectionHeader eyebrow="CASE MANAGEMENT" title="Fraud cases" description="Triage and investigate evidence across all supported modalities." action={<NewInvestigationButton />}/><CasesTable cases={cases}/></div></WorkspaceShell>;
}

