import { backendFetch } from "@/lib/backend";
export async function GET(request: Request) {
  const days = new URL(request.url).searchParams.get("days") ?? "7";
  try {
    return Response.json(await backendFetch(`/analytics/overview?days=${encodeURIComponent(days)}`));
  } catch {
    return Response.json({ detail: "Analytics are temporarily unavailable. Please retry." }, { status: 503 });
  }
}
