---
id: features-limitations
title: Features and Limitations
route: /models
roles: [viewer, analyst, reviewer, admin, executive]
status: implemented-foundation
---
# What is operational?
The baseline includes BEC indicators from supplied authentication data, invoice payment-change signals, selected domain indicators, evidence intake, tenant-scoped cases, versioned scoring, cited narratives, and audit records.

# Is OCR authenticity verification?
No. OCR extracts text and confidence metadata; it does not establish authenticity. Quality depends on language, scan quality, and deployment configuration.

# Are deepfake and identity detectors guaranteed?
No. Experimental adapters must not be described as validated production detection unless approved models and providers are configured.

# What does model health mean?
Healthy means a configured component is reachable; it does not mean every fraud category is covered.
