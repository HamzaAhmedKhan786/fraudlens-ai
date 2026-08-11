import { backendFetch, type CaseSummary } from "@/lib/backend";

export async function POST() {
  const suffix = Date.now().toString().slice(-8);
  const caseId = `FR-${suffix}`;
  try {
    const created = await backendFetch<CaseSummary>("/cases", {
      method: "POST",
      body: JSON.stringify({
        id: caseId,
        tenant_id: "demo",
        subject: "New supplier payment request",
        case_type: "Invoice + email",
      }),
    });
    await backendFetch(`/cases/${caseId}/evidence`, {
      method: "POST",
      body: JSON.stringify({
        id: `${caseId}-email`,
        kind: "email",
        source: "supplier-payment.eml",
        attributes: {
          reply_to_mismatch: true,
          spf_pass: false,
          dkim_pass: true,
          dmarc_pass: false,
        },
      }),
    });
    await backendFetch(`/cases/${caseId}/evidence`, {
      method: "POST",
      body: JSON.stringify({
        id: `${caseId}-invoice`,
        kind: "invoice",
        source: "supplier-invoice.pdf",
        attributes: { iban_changed: true, metadata_modified: true },
      }),
    });
    const report = await backendFetch(`/cases/${caseId}/investigate`, { method: "POST" });
    return Response.json({ case: created, report }, { status: 201 });
  } catch (error) {
    return Response.json(
      { detail: error instanceof Error ? error.message : "Investigation failed" },
      { status: 502 },
    );
  }
}

