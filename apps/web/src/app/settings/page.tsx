import { SettingsForm } from "../ui/settings-form";
import { SectionHeader, WorkspaceShell } from "../ui/workspace-shell";

export default function SettingsPage() {
  return <WorkspaceShell><div className="content section-page"><SectionHeader eyebrow="WORKSPACE" title="Settings" description="Configure safety gates, investigation thresholds, and evidence lifecycle defaults."/><SettingsForm/><div className="notice-box">Environment secrets, Kafka brokers, databases, and model credentials remain deployment configuration and are never exposed to the browser.</div></div></WorkspaceShell>;
}

