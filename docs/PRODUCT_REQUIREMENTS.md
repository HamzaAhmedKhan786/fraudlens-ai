# FraudLens AI Product Requirements

## Product boundary and users

FraudLens is an evidence-centric fraud investigation control plane. It helps individuals, SMEs,
financial operations teams, security analysts, and regulated enterprises collect email/document/
media evidence, run deterministic controls, calculate versioned risk, and record human decisions.
It does not prove authenticity from a single signal: SPF/DKIM/DMARC, low risk, LLM text, or an
administrator approval are supporting evidence, not guarantees.

Implemented foundations include tenant-scoped cases, evidence, uploads, investigations, audit,
Gmail read-only ingestion, header parsing, URL/email/document rules, OCR, attachment validation,
optional ClamAV/Kafka/MinIO, deterministic risk fusion, optional cited LLM narratives, retention,
and human disposition. Video/audio inference adapters are experimental; validated tamper,
identity, and validated media models still require approved providers. OIDC, multi-workspace access,
entitlements, test-mode billing, persistent copilot feedback, and recoverable deletion are implemented.

## Required workflow

`Evidence → deterministic rules → optional grounded LLM analysis → versioned risk fusion → human review → disposition`

Original evidence, automated findings, and audit history remain distinct from human decisions.
Security-critical findings, quarantine, and scores cannot be overridden by the LLM. Protected
decisions require a different authorized actor; a future approval service must enforce this in the
database transaction, not only the UI.

## Requirements matrix

| Feature | Priority | Status | Dependencies | Acceptance criteria | Phase |
|---|---|---|---|---|---|
| Typed/custom investigation intake | P0 | Implemented | Case API | Type, evidence sources, modules persisted; unavailable modules disabled | 1 |
| Case create/view/edit/search/filter | P0 | Partial | PostgreSQL, audit | Tenant-scoped create/read/update; search/risk/type/priority filters complete | 1 |
| Case/evidence soft delete, restore, bulk delete | P0 | Implemented | Retention policy, object store | Permission, audit, 30-day recovery, retention-safe originals | 1 |
| Gmail OAuth and filtered ingestion | P0 | Implemented | Google OAuth/Gmail API | Encrypted tokens, atomic state, revocation, retry, pagination, dedup | 1 |
| Selected-message/add-in intake | P1 | Design only | Provider adapter contract | Signed add-in request imports one RFC822 message with consent | 3 |
| SPF/DKIM/DMARC and sender checks | P0 | Implemented | Raw message headers | Findings cite headers; never alone assert authenticity | 1 |
| URL/domain/attachment controls | P0 | Implemented/conditional | RDAP, ClamAV | Explainable findings; quarantine when configured/required | 1 |
| OCR/document extraction | P0 | Implemented | Tesseract/Poppler | Text, page, confidence, language/status returned | 1 |
| Validated document/image tamper | P1 | Missing | Approved model/weights/evals | Version/confidence/uncertainty and evaluation threshold | 3 |
| Audio/video deepfake | P1 | Experimental adapter | Licensed models, GPU | Explicit experimental result; failures never report success | 3 |
| Deterministic risk and policies | P0 | Implemented | Versioned agents | Reproducible score; tenant threshold; citations | 1 |
| Grounded LLM narrative/copilot | P1 | Implemented/optional | OpenAI, Groq, or Ollama | Cited output only; cannot change score/quarantine | 1 |
| Multi-workspace creation/switching | P0 | Implemented | OIDC memberships | Active membership revalidated; workspace role enforced | 2 |
| Prompt/model guardrails | P0 | Implemented | LLM adapters | Injection patterns blocked; evidence bounded; citations allow-listed | 2 |
| False-positive/admin review queue | P0 | Implemented | Existing disposition/audit | Request, reason, reviewer transition, no self-approval | 1 |
| Executive approval | P1 | Design only | OIDC/RBAC, policy engine | Threshold routing, delegation, expiry, separation of duties | 2 |
| Individual/organization accounts | P0 | Foundation implemented | OIDC, email service | Tenant onboarding, hashed invitations, memberships | 2 |
| RBAC/MFA/SSO | P0 | OIDC/RBAC implemented; MFA provider-owned | Identity provider | Five roles; signed JWT validation; configure IdP MFA | 2 |
| Outlook/Microsoft 365 | P1 | Adapter contract implemented | Entra ID, Graph | Capability/add-in contracts; provider deployment still required | 3 |
| Historical similarity | P1 | Baseline implemented | Evaluated feature service | Tenant-scoped advisory matching; never auto-whitelists | 3 |
| Pricing comparison | P1 | Implemented/provisional | Central plan config | Responsive monthly/annual comparison; billing clearly inactive | 1 |
| Entitlements and usage metering | P0 | Foundation implemented | Auth, usage ledger | Backend case quota; ledgers/limits cover all metrics | 4 |
| Stripe billing | P1 | Prepared, disabled | Stripe approval/webhooks | No live payment path; secure configuration reserved | 4 |
| Transactional outbox | P0 | Implemented producer records | Kafka relay/monitoring | Domain events commit atomically; relay is operational setup | 4 |
| Exportable reports | P1 | Implemented | Case authorization | Authenticated evidence-grounded HTML download | 3 |
| Observability and incident response | P0 | Partial | Metrics/log backend | Correlation IDs, SLOs, alerting, redaction, runbooks | V1 |

## Security, privacy, and operations

- Data minimization, purpose limitation, consent records, regional processing, DPA/subprocessor
  inventory, DSAR export/deletion, legal holds, and configurable retention are required for GDPR.
- OAuth tokens require envelope encryption/key rotation; secrets never reach the browser or logs.
- Object access must be tenant-scoped and short-lived. Malware quarantine is never bypassed by
  review or executive approval. Prompt content is untrusted evidence; LLM tools remain restricted.
- Redis-backed rate limits/idempotency, OIDC/JWT object authorization, backup/restore tests,
  vulnerability management, SLOs, tracing, alerting, and disaster recovery remain commercial gates.

## Economics assumptions

Provisional prices are €9.99 Individual, €49 Small Business, €149 Business Pro, and Enterprise from
€499/month excluding VAT, with an 18% example annual discount. They are not active offers. Before
approval, measure per-tenant storage, OCR CPU time, LLM tokens, email volume, support, and GPU
minutes. Gross margin and break-even must use observed workloads; no margin claim is currently
validated. GPU inference should use explicit credits and scale-to-zero capacity.

## Roadmap

- **MVP / Phase 1:** reliable intake, typed cases, Gmail, uploads, deterministic/LLM pipeline,
  provisional pricing, audit/retention; finish deletion and admin-review transitions.
- **Commercial V1 / Phase 2:** OIDC registration, individual/organization tenants, invitations,
  RBAC/MFA, reviewer queue, executive-approval design implementation, operational SLOs.
- **Expansion / Phase 3:** provider-neutral email adapters, Microsoft Graph, add-ins, consented
  monitoring, validated media models, tenant-safe historical similarity.
- **Enterprise / Phase 4:** backend entitlements, metering, Stripe lifecycle, GPU credits, advanced
  policy/approval engine, compliance exports, regional deployment and enterprise observability.
