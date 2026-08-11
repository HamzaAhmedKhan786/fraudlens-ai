import "@fontsource-variable/inter";
import "./styles.css";
import "./workspace.css";

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
