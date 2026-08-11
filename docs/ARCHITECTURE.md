# FraudLens AI architecture

FraudLens AI starts as a modular monolith with event-driven worker boundaries. This keeps fraud
decisions transactional and auditable while allowing expensive modality analyzers to scale
independently.

## Product shape

The primary product is a multi-tenant web application for analysts and investigators. A later
desktop or endpoint sensor can perform local collection, quarantine, and privacy-sensitive
inference, but it should report evidence to the same control plane.

## Decision boundary

1. Deterministic agents extract and validate evidence.
2. The risk engine applies versioned rules and calibrated weights.
3. The LLM investigator summarizes only cited evidence and may propose additional tools.
4. Policy gates validate tool budgets, citations, and confidence.
5. A human owns consequential decisions.

LLMs never directly set the fraud verdict or mutate evidence.

## Runtime components

- `apps/api`: FastAPI control plane and agent orchestrator.
- `apps/web`: Next.js analyst console.
- Kafka: durable case and analysis events; disabled for lightweight local tests.
- PostgreSQL: cases, evidence, findings, decisions, and audit records.
- Redis: idempotency keys, rate limits, short-lived workflow state.
- MinIO/S3: immutable evidence objects.

## Extraction path

Each analyzer implements the same agent contract. Heavy document, image, video, and audio agents
can later move into dedicated consumers without changing the API or evidence schema.

