---
id: email-connectors
title: Connecting Gmail
route: /connectors
roles: [viewer, analyst, reviewer, admin, executive]
status: implemented-foundation
---
# How do I connect Gmail?
Open Email connectors and select Connect Gmail. Complete Google's consent screen with your authorized account. The deployment administrator must configure Google OAuth and enable the Gmail API. FraudLens requests read-only Gmail access and does not collect your email password.

# How do I import messages?
Create or choose an existing investigation. In Email connectors, select that case, set label, sender, date, and attachment filters, then import a page of messages. Check imported, duplicate, and failed counts and the displayed failure details. Open the case to review imported evidence and explicitly run analysis.

# Why did some messages fail?
Read the per-message error. Verify that the target case exists in this workspace, the Gmail API is enabled, and the connection is authorized. A connection error or revoked consent may require reconnecting.

# Can I use Outlook?
Microsoft 365 is a prepared integration. Check the displayed capability state. Provider credentials and consent must be configured before a connection can become available.
