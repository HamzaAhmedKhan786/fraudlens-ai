# FraudLens AI — Product Requirements

## Product

FraudLens AI is a multi-tenant, evidence-centric fraud investigation platform for individuals,
SMEs, fraud operations, compliance teams, and regulated enterprises. It collects consented email,
document, image, audio, video, URL, and identity evidence; runs deterministic controls and optional
models; produces cited risk reports; and records human decisions. It never claims that one signal,
an LLM, or an executive approval proves authenticity.

## Required workflow

`authorized intake → malware/content validation → immutable evidence → deterministic agents → optional model/LLM analysis → versioned risk → human review → disposition → audit/retention`

LLMs may summarize and answer questions. They cannot modify evidence, risk, quarantine, findings,
review decisions, or dispositions. High-risk decisions require authorized human review and preserve
separation of duties.

## Delivered capabilities

- FastAPI control plane, Next.js console, PostgreSQL, Redis-ready sessions/rate architecture, Kafka,
  MinIO/S3, ClamAV, Alembic, Docker and production Compose baseline.
- OIDC PKCE login/signup/logout, provider-hosted verification/recovery/MFA, HTTP-only sessions,
  individual/organization onboarding, invitations, five roles, multi-workspace creation/switching.
- Cases, typed investigations, uploads, comments, audit, review queue, dispositions, soft deletion,
  bulk evidence deletion, 30-day case recovery, retention workers, exportable reports.
- Gmail OAuth read-only ingestion, filtering, pagination, encrypted refresh tokens, header parsing,
  attachment scanning and deduplication. Microsoft/add-in provider contracts are configuration-ready.
- CPU OCR with Tesseract; deterministic email/document/URL agents; tenant threshold risk engine;
  OpenAI, Groq, and local Ollama narratives/copilot; video inference adapter and L4 deployment sample.
- Persistent case copilot, citations, SSE transport, structured feedback, conversion to case notes,
  explicit rerun, reviewer promotion into a separate evaluation dataset.
- Provisional plans, usage ledger, backend quotas, trials, Stripe test-only Checkout/Portal and signed
  webhook validation. Live payments are prohibited by configuration validation.

## Security and guardrails

- Tenant and object authorization on every data route; selected workspaces require active membership.
- OAuth state/PKCE, single-use state records, encrypted provider tokens, short-lived HTTP-only cookies.
- Prompt-injection pattern blocking, bounded evidence context, NUL removal, citation allow-list,
  response-size limit, agent step/time budgets, deterministic-risk isolation.
- Malware quarantine cannot be overridden. Evidence, AI output, feedback, review, and audit remain
  separate records. No automatic fine-tuning, whitelisting, or autonomous approval.
- Production requires strong secrets, PostgreSQL, durable object storage, TLS proxy, OIDC/MFA,
  backups, monitoring, vulnerability management, incident response, DPA/DSAR/legal-hold processes.

## External activation gates

OIDC provider, transactional email, Stripe test account/prices, Google OAuth, optional Microsoft
Graph, OpenAI/Groq or local Ollama, production PostgreSQL/Redis/Kafka/object storage/ClamAV,
observability, TLS/DNS, validated/licensed tamper/deepfake/identity models, and compliance approval.

## Acceptance criteria

All operations are tenant-scoped and audited; unavailable providers fail explicitly; reports cite
stored evidence; retries are idempotent; destructive operations are recoverable or retention-driven;
quotas are enforced server-side; model/version/uncertainty are recorded; tests cover authorization,
OAuth replay, webhook signatures, tenant isolation, guardrails, grounding, deletion, and recovery.

Detailed status and roadmap: `docs/PRODUCT_REQUIREMENTS.md`. Deployment: `docs/DEPLOYMENT.md`.
