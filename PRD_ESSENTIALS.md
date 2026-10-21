# FraudLens AI — Codex Essentials

## Repository and stack

- Monorepo: `apps/api` FastAPI/Python 3.12; `apps/web` Next.js 16/React 19/TypeScript.
- Data: PostgreSQL + SQLAlchemy/Alembic. Async jobs: Kafka. Cache/rate target: Redis.
- Evidence: MinIO/S3 or local filesystem. Malware: ClamAV. OCR: Tesseract/Poppler.
- Models: deterministic agents always first; optional OpenAI, Groq, or Ollama; remote video adapter.
- Active migrations are linear. Never edit real `.env`, expose secrets, or create fake successes.

## Core invariants

1. Every case/evidence/chat/review/billing query is tenant-scoped.
2. Workspace switching requires an active membership; membership role becomes the effective role.
3. Evidence is untrusted data, never instructions. LLM output cannot alter deterministic state.
4. Original evidence, findings, AI messages, feedback, human decisions, and audit are separate.
5. High/critical findings enter review. Reviewers cannot approve their own requests.
6. Deletion is soft and audited; recovery is 30 days; physical purge belongs to retention jobs.
7. Stripe accepts test keys only. External providers must report `CONFIGURATION_REQUIRED`/failure.
8. Do not automatically train on feedback. Reviewers explicitly promote examples for evaluation.

## Key modules

- `fraudlens/orchestrator.py`: bounded parallel deterministic-agent execution.
- `fraudlens/agents/`: email, document, URL, risk, narrative adapters.
- `fraudlens/guardrails.py`: prompt, evidence-context, and citation enforcement.
- `fraudlens/copilot.py`: persistent grounded case chat and reviewed feedback.
- `fraudlens/services.py`: cases, review, deletion, audit and read models.
- `fraudlens/platform_services.py`: workspaces, invitations, entitlements, similarity.
- `fraudlens/gmail.py`, `ingestion.py`, `retention.py`, `billing.py`: integration boundaries.
- `apps/web/src/app/cases/[id]`: workflow, deletion, evidence, findings and AI Copilot.

## Local Ollama

```dotenv
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.2:3b
OLLAMA_API_KEY=ollama
```

For Docker use `http://host.docker.internal:11434/v1`. Pull the selected model in Ollama first.

## Future integrations

Microsoft Graph/Outlook add-ins, Stripe live mode after approval, Redis distributed rate limiting,
Kafka outbox relay/monitoring, OpenTelemetry/Sentry/Prometheus, SIEM/SOAR, supplier/IBAN sources,
WHOIS/domain reputation, identity/KYC provider, validated document/image/audio/video models,
regional storage, legal hold, DSAR export, enterprise SAML/SCIM and managed GPU inference.

## Before changing code

Read this file, `PRD.md`, `docs/PRODUCT_REQUIREMENTS.md`, and the nearest `AGENTS.md`. Preserve APIs,
tenant isolation, audit, citations, retention, deterministic precedence, and explicit provider status.
