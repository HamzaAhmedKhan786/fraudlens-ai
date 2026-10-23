# Remaining work and activation gates

Status reviewed 2026-10-23 against the PRD, deployment guide and selected implementation paths.
This is a prioritized release checklist, not a claim of a completed production security audit.
Existing foundations should be reused, not rebuilt.

## Configure and validate existing functionality

| Priority | Area | Remaining action / evidence required |
| --- | --- | --- |
| P0 | Identity and onboarding | Configure the OIDC issuer/client/redirects and provider-hosted verification, recovery and MFA; exercise registration, invitations, workspace isolation, logout and all five roles end to end. Do not add local password storage. |
| P0 | Deployment | Supply production DNS/TLS, secret manager, PostgreSQL, Redis, Kafka, object storage and ClamAV; run migrations and deployment scripts in staging, then backup/restore and retention drills. The Compose profile is a single-host baseline, not HA. |
| P0 | Gmail and OCR | Validate fresh OAuth, revoked tokens, pagination, filters, attachments and deduplication with consented test mail; install/verify the seven Tesseract language packs and PDF tooling on each target host. Implementation does not prove authenticity. |
| P1 | Subscription activation | Configure Stripe **test** keys, plan price IDs, webhook signing secret and Portal; validate trial/state transitions, replay handling and usage reconciliation. Prices require business approval; do not enable live payments. |
| P1 | LLM providers | Configure approved OpenAI/Groq credentials or a pulled Ollama model and endpoint; evaluate grounding, injection resistance, unavailable-provider behavior and performance with representative evidence. |

## Engineering still required or needing completion

| Priority | Area | Remaining implementation / acceptance gate |
| --- | --- | --- |
| P0 | Distributed controls | Complete/verify Redis-backed distributed rate limiting and idempotency across workers. Make quota reservation atomic under concurrent requests and validate every billable metric, not only UI usage totals. |
| P0 | Event delivery and operations | Complete the operational Kafka outbox relay, delivery/retry monitoring and alerts; prove replay/recovery under failure. Add centralized redacted logs, metrics/tracing, SLOs and incident runbooks. |
| P0 | Release validation | Add repeatable browser E2E coverage for login, workspaces, Gmail, uploads, reviews, deletion/restore, quotas and test billing; run PostgreSQL/concurrency, load, accessibility and security tests. Manual screenshot checks are not an E2E suite. |
| P1 | Outlook and inbox add-ins | Implement Microsoft Graph OAuth/ingestion beyond the current provider contract; package Gmail/Outlook selected-message add-ins and consented monitoring, token renewal and webhook lifecycle handling. |
| P1 | Validated detectors | Select licensed document/image tamper, audio/video spoofing and identity providers/models; build validated adapters, evaluation datasets and calibrated uncertainty. GPU configuration samples are not deployed inference services. |
| P1 | Trusted intelligence | Integrate authoritative supplier/IBAN history and approved reputation sources. Add verified geographic records with provenance and privacy rules before enabling risk-map markers. A country outline is not a threat observation. |
| P1 | Copilot streaming and approvals | Current case SSE emits chunks after the answer has been generated: implement genuine incremental provider streaming and wire an interruptible client where appropriate. Complete policy-driven executive escalation with transactional separation of duties; preserve findings. |
| P1 | Privacy and enterprise readiness | Complete DSAR export/deletion, legal holds, key rotation, regional-processing controls and DPA/subprocessor documentation. Enterprise SAML/SCIM, SIEM/SOAR and HA/DR remain separate roadmap work. |

## Suggested order

1. Activate OIDC and test existing Gmail/OCR with real, consented data in staging.
2. Harden distributed quotas/idempotency, event delivery and observability; add automated E2E tests.
3. Validate Stripe test lifecycle and deployment/restore procedures.
4. Implement Outlook/add-ins, trusted intelligence and evaluated model integrations.

No secrets, live payment activation, GPU provisioning or production deployment are included in
the screenshot/README update. See `PRD.md`, `docs/PRODUCT_REQUIREMENTS.md` and
`docs/DEPLOYMENT.md` for the existing architecture and broader requirements.
