import { backendFetch, type AgentStatus } from "@/lib/backend";
import type { Overview, CasePage } from "@/lib/analytics-types";
import { CommandCenter } from "./ui/command-center";
import { WorkspaceShell } from "./ui/workspace-shell";

export default async function Dashboard() {
  const [overview, cases, agents] = await Promise.all([
    backendFetch<Overview>("/analytics/overview?days=7").catch(() => null),
    backendFetch<CasePage>("/cases/search?page_size=6").catch(() => null),
    backendFetch<AgentStatus[]>("/agents").catch(() => null),
  ]);
  return <WorkspaceShell><CommandCenter initial={overview} cases={cases} agents={agents}/></WorkspaceShell>;
}
