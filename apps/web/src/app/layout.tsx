import "@fontsource-variable/inter";
import "./tailwind.css";
import "./styles.css";
import "./workspace.css";
import "./ingestion.css";
import "./workflow.css";
import "./risk-gauge.css";
import "./intelligence.css";
import "./connectors.css";
import "./investigation.css";
import "./pricing.css";
import "./enterprise.css";
import { GuidanceCopilot } from "./ui/guidance-copilot";

export const metadata = {
  title: "FraudLens AI | Investigation Console",
  description: "Multimodal agentic fraud intelligence platform",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}<GuidanceCopilot/></body>
    </html>
  );
}
