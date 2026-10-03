import { backendFetch, type PolicyDefinition } from "@/lib/backend";

export async function PUT(request: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  return Response.json(await backendFetch<PolicyDefinition>(`/policies/${encodeURIComponent(id)}`, {
    method: "PUT", body: JSON.stringify(await request.json()),
  }));
}
