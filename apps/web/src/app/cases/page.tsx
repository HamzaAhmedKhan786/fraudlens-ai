import { backendFetch } from "@/lib/backend";
import type { CasePage } from "@/lib/analytics-types";
import { CaseSearchTable } from "../ui/case-search-table";
import { NewInvestigationButton } from "../ui/new-investigation";
import { SectionHeader, WorkspaceShell } from "../ui/workspace-shell";

export default async function CasesPage({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const { q = "" } = await searchParams;
  const data = await backendFetch<CasePage>(`/cases/search?q=${encodeURIComponent(q)}`).catch(() => null);
  return <WorkspaceShell><div className="content section-page"><SectionHeader eyebrow="CASE MANAGEMENT" title="Your investigations, in focus" description="Track evidence, assess deterministic risk, and collaborate on every decision." action={<NewInvestigationButton/>}/><CaseSearchTable initial={data} initialQuery={q}/></div></WorkspaceShell>;
}
