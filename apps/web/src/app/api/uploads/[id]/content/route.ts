import { backendAuthHeaders, backendBaseUrl } from "@/lib/backend";

export async function GET(_request: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  const response = await fetch(`${backendBaseUrl}/uploads/${encodeURIComponent(id)}/content`, {
    headers: await backendAuthHeaders(), cache: "no-store",
  });
  return new Response(response.body, { status: response.status, headers: response.headers });
}
