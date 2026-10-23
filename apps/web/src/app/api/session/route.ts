import { backendFetch } from "@/lib/backend";
export async function GET() {
  try { return Response.json(await backendFetch("/session")); }
  catch { return Response.json({ detail: "Session unavailable" }, { status: 503 }); }
}
