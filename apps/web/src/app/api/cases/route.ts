import { backendFetch, type CaseSummary } from "@/lib/backend";

export async function GET() {
  try {
    return Response.json(await backendFetch<CaseSummary[]>("/cases"));
  } catch (error) {
    return Response.json(
      { detail: error instanceof Error ? error.message : "Backend unavailable" },
      { status: 503 },
    );
  }
}

