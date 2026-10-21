---
id: troubleshooting
title: Troubleshooting
route: /
roles: [viewer, analyst, reviewer, admin, executive]
status: implemented-foundation
---
# Why is investigation data missing?
Check API connectivity and persisted cases and reports. Do not confuse an unavailable-data fallback with healthy zero activity.

# Why was a file rejected?
Verify extension, content signature, size, permissions, and reported security status. Never work around quarantine.

# Why is the AI answer limited?
The configured provider may be unavailable or verified documentation may not support the claim. The assistant should abstain and suggest the appropriate page.
