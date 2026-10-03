import { backendFetch, type CaseDetail } from "@/lib/backend";

export async function PATCH(request: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  return Response.json(await backendFetch<CaseDetail>(`/cases/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: JSON.stringify(await request.json()),
  }));
}
