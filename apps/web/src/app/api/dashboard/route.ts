import { backendFetch, type DashboardMetrics } from "@/lib/backend";

export async function GET() {
  try {
    return Response.json(await backendFetch<DashboardMetrics>("/dashboard"));
  } catch (error) {
    return Response.json(
      { detail: error instanceof Error ? error.message : "Backend unavailable" },
      { status: 503 },
    );
  }
}

