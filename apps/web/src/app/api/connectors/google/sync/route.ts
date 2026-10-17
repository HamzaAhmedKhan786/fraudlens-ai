import { backendFetch, type GmailSyncResult } from "@/lib/backend";

export async function POST(request: Request) {
  try { return Response.json(await backendFetch<GmailSyncResult>("/connectors/google/sync", { method: "POST", body: JSON.stringify(await request.json()) })); }
  catch (error) { return Response.json({ detail: error instanceof Error ? error.message : "Sync failed" }, { status: 502 }); }
}
