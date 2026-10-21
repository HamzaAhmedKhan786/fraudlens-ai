import {
  backendAuthHeaders,
  backendBaseUrl,
  backendFetch,
  type UploadList,
} from "@/lib/backend";

export async function GET(request: Request) {
  try {
    const url = new URL(request.url);
    const caseId = url.searchParams.get("case_id");
    const suffix = caseId ? `?case_id=${encodeURIComponent(caseId)}` : "";
    return Response.json(await backendFetch<UploadList>(`/uploads${suffix}`));
  } catch (error) {
    return Response.json(
      { detail: error instanceof Error ? error.message : "Backend unavailable" },
      { status: 503 },
    );
  }
}

export async function POST(request: Request) {
  const form = await request.formData();
  const caseId = form.get("case_id");
  const file = form.get("file");
  if (typeof caseId !== "string" || !(file instanceof File)) {
    return Response.json({ detail: "case_id and file are required" }, { status: 400 });
  }
  const outgoing = new FormData();
  outgoing.set("file", file);
  try {
    const response = await fetch(
      `${backendBaseUrl}/cases/${encodeURIComponent(caseId)}/uploads`,
      { method: "POST", headers: await backendAuthHeaders(), body: outgoing },
    );
    return new Response(await response.arrayBuffer(), {
      status: response.status,
      headers: { "Content-Type": response.headers.get("Content-Type") ?? "application/json" },
    });
  } catch (error) {
    return Response.json(
      { detail: error instanceof Error ? error.message : "Upload service unavailable" },
      { status: 503 },
    );
  }
}

