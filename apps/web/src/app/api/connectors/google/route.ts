import { backendFetch, type GmailConnection } from "@/lib/backend";

export async function GET() {
  try { return Response.json(await backendFetch<GmailConnection>("/connectors/google")); }
  catch (error) { return Response.json({ detail: error instanceof Error ? error.message : "Backend unavailable" }, { status: 503 }); }
}

export async function DELETE() {
  try { await backendFetch("/connectors/google", { method: "DELETE" }); return new Response(null, { status: 204 }); }
  catch (error) { return Response.json({ detail: error instanceof Error ? error.message : "Disconnect failed" }, { status: 502 }); }
}
