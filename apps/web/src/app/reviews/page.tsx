import { backendFetch, type ReviewRequest } from "@/lib/backend";
import { SectionHeader, WorkspaceShell } from "../ui/workspace-shell";
import { ReviewQueue } from "./review-queue";
export default async function ReviewsPage(){const rows=await backendFetch<ReviewRequest[]>("/reviews").catch(()=>[]);return <WorkspaceShell><div className="content section-page"><SectionHeader eyebrow="HUMAN REVIEW" title="Admin review queue" description="Protected, audited decisions remain separate from automated findings."/><ReviewQueue initial={rows}/></div></WorkspaceShell>}
