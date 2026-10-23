import { backendFetch } from "@/lib/backend";
export async function POST(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  try {
    return Response.json(await backendFetch(`/cases/${encodeURIComponent(id)}/reviews`, {
      method: "POST", body: JSON.stringify(await request.json()),
    }), { status: 201 });
  } catch {
    return Response.json({ detail: "Review request could not be saved. Check your permissions and reason." }, { status: 502 });
  }
}
