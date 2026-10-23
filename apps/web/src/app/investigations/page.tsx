import { backendFetch, type InvestigationSummary } from "@/lib/backend";
import { NewInvestigationButton } from "../ui/new-investigation";
import { RunHistory } from "../ui/run-history";
import { SectionHeader, WorkspaceShell } from "../ui/workspace-shell";
export default async function InvestigationsPage() {
  const rows = await backendFetch<InvestigationSummary[]>("/investigations").catch(() => null);
  return <WorkspaceShell><div className="content section-page"><SectionHeader eyebrow="INVESTIGATION OPERATIONS" title="Every analysis, accounted for" description="Review recorded agent runs, deterministic assessments, and their supporting evidence." action={<NewInvestigationButton/>}/><RunHistory initial={rows}/></div></WorkspaceShell>;
}
