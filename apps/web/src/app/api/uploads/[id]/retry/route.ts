import { backendFetch, type UploadSummary } from "@/lib/backend";

export async function POST(
  _request: Request,
  context: { params: Promise<{ id: string }> },
) {
  const { id } = await context.params;
  try {
    return Response.json(
      await backendFetch<UploadSummary>(`/uploads/${encodeURIComponent(id)}/retry`, {
        method: "POST",
      }),
    );
  } catch (error) {
    return Response.json(
      { detail: error instanceof Error ? error.message : "Retry failed" },
      { status: 502 },
    );
  }
}
