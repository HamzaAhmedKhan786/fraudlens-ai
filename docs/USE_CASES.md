# FraudLens use cases and decision semantics

## Risk levels

FraudLens produces a deterministic score from 0 to 100. Each finding contributes configured risk
points multiplied by its confidence; the total is capped at 100. The LLM narrative never changes
the score.

| Score | Level | Operational response |
| --- | --- | --- |
| 0–29 | Low | Monitor and validate the evidence. |
| 30–59 | Medium | Analyst review. |
| 60–79 | High | Expedited analyst review. |
| 80–100 | Critical | Immediate human review and protective action according to policy. |

Critical does not mean that fraud is proven. It means that the combined deterministic indicators
crossed the escalation threshold. Examples include an email-authentication failure plus a Reply-To
mismatch plus an unverified invoice bank-account change. A normal document should remain low risk;
merely uploading a PDF, DOCX, image, or text file is not suspicious.

## Operational now

- Business-email-compromise indicators supplied by trusted email parsing: Reply-To mismatch and
  SPF, DKIM, or DMARC failure.
- Invoice and payment-change triage: changed-account assertions, suspicious bank-detail-change
  language, urgent payment language, IBAN extraction, and document metadata assertions.
- Recently registered URL/domain indicators when domain-age enrichment is supplied.
- Evidence intake for EML, PDF, DOCX, TXT, PNG, and JPEG with type validation, SHA-256
  deduplication, retention metadata, quarantine state, and an audit trail.
- Optional ClamAV malware scanning before parsing. Malware is a file-security decision, not a fraud
  score: infected files are quarantined and never analyzed as ordinary evidence.
- Tenant-scoped case workflow, deterministic scoring, cited narratives, comments, disposition,
  policies, audit records, and evidence downloads.

## High-value next integrations

1. Email gateway ingestion with verified SPF/DKIM/DMARC results, attachment expansion, sender
   impersonation, look-alike domains, and URL reputation.
2. Supplier master-data comparison so IBAN, address, tax ID, invoice totals, and payment terms can
   be compared with trusted historical values.
3. OCR for scanned invoices and identity documents, followed by field extraction and consistency
   checks.
4. Document tamper vision for copy-move, font/layout inconsistency, metadata conflict, and image
   compositing detection.
5. Identity verification with document authenticity, selfie matching, liveness, and sanctions/PEP
   provider adapters where legally permitted.
6. Video and audio deepfake detection using calibrated providers, model-version tracking, and
   human-review thresholds.
7. Transaction monitoring: velocity, amount deviation, beneficiary novelty, device reuse, and
   mule-account network indicators.
8. Account takeover and onboarding risk using device, IP, session, behavioral, and identity
   signals.
9. Claims and marketplace fraud using duplicate media, altered receipts, entity reuse, and graph
   relationships.
10. Continuous entity intelligence across emails, domains, bank accounts, people, companies,
    phones, devices, cases, and transactions.

## Model readiness language

`HEALTHY` means an implemented component is available, not that every possible fraud type is
covered. `NOT_CONFIGURED` means an adapter or approved model is still required. Every learned model
must be evaluated against representative data, calibrated, versioned, monitored for drift, and
kept behind human review before it can be described as production-ready.
