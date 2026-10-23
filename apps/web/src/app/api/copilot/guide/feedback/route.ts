import { backendFetch } from "@/lib/backend";
export async function POST(request: Request) {
  try {
    return Response.json(await backendFetch("/copilot/guide/feedback", {
      method: "POST", body: JSON.stringify(await request.json()),
    }), { status: 201 });
  } catch {
    return Response.json({ detail: "Feedback could not be saved." }, { status: 503 });
  }
}
