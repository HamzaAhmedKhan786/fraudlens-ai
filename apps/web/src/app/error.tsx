"use client";
import { WorkspaceShell } from "./ui/workspace-shell";
import { EmptyState } from "./ui/empty-state";
export default function ErrorPage({ retry }: { error: Error & { digest?: string }; retry: () => void }) {
  return <WorkspaceShell><div className="content"><section className="panel" role="alert"><EmptyState title="This workspace could not be loaded" description="Retry to reconnect. Your saved investigations remain available once the service recovers." action={<button className="primary" onClick={retry}>Retry loading</button>}/></section></div></WorkspaceShell>;
}
