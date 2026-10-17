import { backendFetch, type PublicIntelligence } from "@/lib/backend";

export async function GET() {
  try { return Response.json(await backendFetch<PublicIntelligence[]>("/intelligence/public")); }
  catch (error) { return Response.json({ detail: error instanceof Error ? error.message : "Backend unavailable" }, { status: 503 }); }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    return Response.json(await backendFetch<PublicIntelligence>("/intelligence/domain", { method: "POST", body: JSON.stringify(body) }), { status: 201 });
  } catch (error) { return Response.json({ detail: error instanceof Error ? error.message : "Lookup failed" }, { status: 502 }); }
}
