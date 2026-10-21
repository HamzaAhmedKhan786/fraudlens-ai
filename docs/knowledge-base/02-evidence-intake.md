---
id: evidence-intake
title: Evidence Intake
route: /uploads
roles: [viewer, analyst, reviewer, admin, executive]
status: implemented-foundation
---
# Which files can I submit?
Supported intake includes EML, PDF, DOCX, TXT, PNG and JPEG up to 50 MB. Permissions and deployment settings can impose lower limits.

# How are uploads handled?
FraudLens validates content signatures, calculates SHA-256 hashes, supports malware scanning and quarantine, and parses accepted files. Infected files are not analyzed as normal evidence.

# Does uploading make a file suspicious?
No. A normal document is not suspicious merely because it was uploaded.

# What if processing fails?
Check upload status and the reported error. Never bypass quarantine; contact an administrator if retry is unavailable.
