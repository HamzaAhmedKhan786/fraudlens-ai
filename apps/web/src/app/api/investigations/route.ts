import { backendFetch, type CaseSummary } from "@/lib/backend";

type NewCaseRequest = { subject?: string; case_type?: string; analysis_modules?: string[]; evidence_sources?: string[] };

export async function POST(request: Request) {
  const payload = (await request.json().catch(() => ({}))) as NewCaseRequest;
  const subject = payload.subject?.trim() ?? "";
  const caseType = payload.case_type?.trim() ?? "";
  if (subject.length < 3 || subject.length > 240 || caseType.length < 2 || caseType.length > 80) {
    return Response.json({ detail: "Enter a valid case title and investigation type." }, { status: 422 });
  }
  const suffix = `${Date.now().toString(36)}${crypto.randomUUID().slice(0, 4)}`.toUpperCase();
  const caseId = `FR-${suffix}`;
  try {
    const created = await backendFetch<CaseSummary>("/cases", {
      method: "POST",
      body: JSON.stringify({
        id: caseId,
        tenant_id: "demo",
        subject,
        case_type: caseType,
        analysis_modules: payload.analysis_modules ?? [],
        evidence_sources: payload.evidence_sources ?? [],
      }),
    });
    return Response.json({ case: created }, { status: 201 });
  } catch (error) {
    return Response.json(
      { detail: error instanceof Error ? error.message : "Case creation failed" },
      { status: 502 },
    );
  }
}

