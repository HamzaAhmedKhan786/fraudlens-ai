import { backendFetch } from "@/lib/backend";
export async function GET(request: Request) {
  const incoming = new URL(request.url).searchParams;
  const params = new URLSearchParams();
  for (const key of ["q", "severity", "status", "sort", "page", "page_size"]) {
    const value = incoming.get(key);
    if (value) params.set(key, value);
  }
  try {
    return Response.json(await backendFetch(`/cases/search?${params}`));
  } catch {
    return Response.json({ detail: "Cases are temporarily unavailable. Please retry." }, { status: 503 });
  }
}
