import { backendFetch } from "@/lib/backend";

export async function POST(request: Request) {
  try {
    return Response.json(await backendFetch("/copilot/guide", {
      method: "POST",
      body: JSON.stringify(await request.json()),
    }));
  } catch (error) {
    return Response.json(
      { detail: error instanceof Error ? error.message : "Guide unavailable" },
      { status: 502 },
    );
  }
}
