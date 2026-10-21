import "@fontsource-variable/inter";
import "./styles.css";
import "./workspace.css";
import "./ingestion.css";
import "./workflow.css";
import "./risk-gauge.css";
import "./intelligence.css";
import "./connectors.css";
import "./investigation.css";
import "./pricing.css";

export const metadata = {
  title: "FraudLens AI | Investigation Console",
  description: "Multimodal agentic fraud intelligence platform",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
