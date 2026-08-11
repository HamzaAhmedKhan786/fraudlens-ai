import { SectionHeader, WorkspaceShell } from "../ui/workspace-shell";
import { UploadConsole } from "../ui/upload-console";

export default function UploadsPage() {
  return <WorkspaceShell><div className="content section-page"><SectionHeader eyebrow="SECURE INTAKE" title="Evidence ingestion" description="Upload, scan, quarantine, process, and monitor evidence across active fraud cases."/><UploadConsole/></div></WorkspaceShell>;
}

