import { backendFetch, type WorkspaceSettings } from "@/lib/backend";

export async function GET() {
  return Response.json(await backendFetch<WorkspaceSettings>("/settings"));
}

export async function PUT(request: Request) {
  return Response.json(await backendFetch<WorkspaceSettings>("/settings", {
    method: "PUT",
    body: JSON.stringify(await request.json()),
  }));
}
