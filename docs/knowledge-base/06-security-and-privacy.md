---
id: security-privacy
title: Access Controls and Privacy
route: /settings
roles: [viewer, analyst, reviewer, admin, executive]
status: implemented-foundation
---
# Who can access case evidence?
Case information is tenant-scoped and authorization is enforced by the backend. The product guide retrieves published documentation, never customer evidence.

# Can the assistant reveal credentials?
No. It must not disclose API keys, access tokens, service credentials, or secret configuration.

# Can the guide take actions?
No. Product-document retrieval is read-only. Action tools require separate authorization, explicit intent, and audit logging.
