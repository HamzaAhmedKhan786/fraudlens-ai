import { backendFetch } from "@/lib/backend";

export async function POST(request: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  return Response.json(await backendFetch(`/cases/${encodeURIComponent(id)}/comments`, {
    method: "POST",
    body: JSON.stringify(await request.json()),
  }), { status: 201 });
}
