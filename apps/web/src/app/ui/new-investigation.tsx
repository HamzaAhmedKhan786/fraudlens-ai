"use client";

import { Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

export function NewInvestigationButton() {
  const router = useRouter();
  const [state, setState] = useState<"idle" | "running" | "failed">("idle");

  async function launch() {
    setState("running");
    const response = await fetch("/api/investigations", { method: "POST" });
    if (!response.ok) {
      setState("failed");
      return;
    }
    setState("idle");
    router.refresh();
  }

  return (
    <button className="primary" onClick={launch} disabled={state === "running"}>
      <Sparkles size={16} />
      {state === "running" ? "Investigating…" : state === "failed" ? "Retry investigation" : "New investigation"}
    </button>
  );
}

