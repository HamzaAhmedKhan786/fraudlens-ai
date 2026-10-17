import { backendFetch } from "@/lib/backend";

export async function POST() {
  try { return Response.json(await backendFetch("/connectors/google/authorize", { method: "POST" })); }
  catch (error) { return Response.json({ detail: error instanceof Error ? error.message : "Authorization failed" }, { status: 502 }); }
}
