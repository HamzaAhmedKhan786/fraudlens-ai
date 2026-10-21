import { backendFetch, type CaseDetail } from "@/lib/backend";

export async function PATCH(request: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  return Response.json(await backendFetch<CaseDetail>(`/cases/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: JSON.stringify(await request.json()),
  }));
}

export async function DELETE(request: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  return Response.json(await backendFetch(`/cases/${encodeURIComponent(id)}`, {
    method: "DELETE", body: JSON.stringify(await request.json()),
  }));
}
